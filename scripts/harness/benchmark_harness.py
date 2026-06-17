#!/usr/bin/env python3
"""
Almanac Benchmark Harness — Smoke Gate + ANN-Benchmarks runner.

Usage:
    python benchmark_harness.py --adapter pinecone --dataset sift1m --metric cosine
    python benchmark_harness.py --adapter qdrant --dataset glove-100 --metric cosine

The harness loads a frozen adapter, runs the smoke gate, then executes
ANN-Benchmarks on the requested dataset. Results are written as JSON to
benchmarks/ann-benchmarks/<tool>-<dataset>-<date>.json.
"""

import argparse
import json
import time
import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import numpy as np


# Add adapters directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adapters"))

from base_adapter import VectorDBAdapter


def load_adapter(adapter_name: str, config: dict) -> VectorDBAdapter:
    """Dynamically load an adapter module and instantiate."""
    module_path = Path(__file__).parent.parent / "adapters" / f"{adapter_name}_adapter.py"
    spec = importlib.util.spec_from_file_location(f"{adapter_name}_adapter", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{adapter_name}_adapter"] = module
    spec.loader.exec_module(module)

    class_name = f"{adapter_name.title()}Adapter"
    if adapter_name == "pgvector":
        class_name = "PgvectorAdapter"
    elif adapter_name == "elasticsearch":
        class_name = "ElasticsearchAdapter"
    elif adapter_name == "opensearch":
        class_name = "OpensearchAdapter"
    elif adapter_name == "redis-vector":
        class_name = "RedisVectorAdapter"
    elif adapter_name == "lancedb":
        class_name = "LancedbAdapter"

    adapter_class = getattr(module, class_name)
    return adapter_class(config)


def generate_synthetic_data(count: int, dimension: int, seed: int = 42) -> tuple:
    """Generate synthetic vectors, IDs, and metadata for smoke gate."""
    rng = np.random.default_rng(seed)
    vectors = rng.random((count, dimension)).astype(np.float32).tolist()
    ids = [f"vec-{i:04d}" for i in range(count)]
    metadata = [
        {
            "title": f"Document {i}",
            "category": "tech" if i % 3 == 0 else "finance" if i % 3 == 1 else "science",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        for i in range(count)
    ]
    return vectors, ids, metadata


def compute_recall_at_k(ground_truth: List[List[str]], results: List[List[str]], k: int) -> float:
    """Compute recall@k against brute-force ground truth."""
    recalls = []
    for gt, res in zip(ground_truth, results):
        gt_set = set(gt[:k])
        res_set = set(res[:k])
        if gt_set:
            recalls.append(len(gt_set & res_set) / len(gt_set))
    return sum(recalls) / len(recalls) if recalls else 0.0


def brute_force_search(vectors: List[List[float]], queries: List[List[float]], top_k: int, metric: str) -> List[List[str]]:
    """Brute-force exact search for ground truth."""
    import numpy as np
    X = np.array(vectors)
    Q = np.array(queries)

    if metric == "cosine":
        X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-10)
        Q_norm = Q / (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-10)
        scores = Q_norm @ X_norm.T
        indices = np.argsort(-scores, axis=1)[:, :top_k]
    elif metric == "euclidean":
        distances = np.linalg.norm(X[None, :, :] - Q[:, None, :], axis=2)
        indices = np.argsort(distances, axis=1)[:, :top_k]
    else:  # dot_product
        scores = Q @ X.T
        indices = np.argsort(-scores, axis=1)[:, :top_k]

    return [[f"vec-{idx:04d}" for idx in row] for row in indices]


def smoke_gate(adapter: VectorDBAdapter, dimension: int, metric: str) -> dict:
    """
    Run the smoke gate:
    1. Create collection with dimension and metric
    2. Insert 1,000 vectors with metadata
    3. Query and verify recall@10 > 0.8 against brute-force ground truth
    """
    print(f"\n=== Smoke Gate: {adapter.__class__.__name__} ===")
    results = {"passed": False, "setup_time_ms": 0, "insert_time_ms": 0, "index_time_ms": 0, "recall_at_10": 0.0, "errors": []}

    # Turn 1: Setup
    t0 = time.time()
    try:
        adapter.setup(dimension=dimension, distance_metric=metric)
        results["setup_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Setup: {results['setup_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"setup failed: {e}")
        print(f"  FAILED: {e}")
        return results

    # Turn 2: Insert 1,000 vectors
    vectors, ids, metadata = generate_synthetic_data(1000, dimension, seed=42)
    t0 = time.time()
    try:
        adapter.load(vectors, ids, metadata)
        results["insert_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Insert 1,000 vectors: {results['insert_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"load failed: {e}")
        print(f"  FAILED: {e}")
        return results

    # Build index + await
    t0 = time.time()
    try:
        adapter.build_index("hnsw", params={"m": 16, "ef_construction": 64})
        adapter.await_ready()
        results["index_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Build index + await: {results['index_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"build_index failed: {e}")
        print(f"  FAILED: {e}")
        return results

    # Turn 3: Query and verify recall
    query_vectors = vectors[:10]  # Use first 10 vectors as queries (self-search)
    try:
        ann_results = []
        for qv in query_vectors:
            res = adapter.search(qv, top_k=10)
            ann_results.append([r["id"] for r in res])

        # Ground truth via brute force
        gt = brute_force_search(vectors, query_vectors, 10, metric)
        recall = compute_recall_at_k(gt, ann_results, 10)
        results["recall_at_10"] = round(recall, 4)
        print(f"  Recall@10: {recall:.4f}")

        if recall > 0.8:
            results["passed"] = True
            print("  SMOKE GATE PASSED")
        else:
            results["errors"].append(f"recall@10 {recall:.4f} below threshold 0.8")
            print(f"  SMOKE GATE FAILED: recall too low")
    except Exception as e:
        results["errors"].append(f"search failed: {e}")
        print(f"  FAILED: {e}")

    return results


def run_ann_benchmark(adapter: VectorDBAdapter, dataset_name: str, metric: str) -> dict:
    """
    Run ANN-Benchmarks on a synthetic dataset (SIFT1M or GloVe-100 style).
    In production, this loads real datasets from benchmarks/data/.
    """
    print(f"\n=== ANN Benchmark: {dataset_name} ===")
    results = {
        "dataset": dataset_name,
        "metric": metric,
        "recall_at_1": 0.0,
        "recall_at_10": 0.0,
        "recall_at_100": 0.0,
        "latency_p50_ms": 0.0,
        "latency_p95_ms": 0.0,
        "latency_p99_ms": 0.0,
        "index_build_time_ms": 0,
        "qps": 0.0,
        "errors": []
    }

    # Synthetic dataset sizes
    config = {
        "sift1m": {"n_vectors": 100000, "n_queries": 100, "dim": 128},
        "glove-100": {"n_vectors": 100000, "n_queries": 100, "dim": 100},
    }.get(dataset_name, {"n_vectors": 100000, "n_queries": 100, "dim": 384})

    dim = config["dim"]
    n_vectors = config["n_vectors"]
    n_queries = config["n_queries"]

    # Setup
    try:
        adapter.setup(dimension=dim, distance_metric=metric)
    except Exception as e:
        results["errors"].append(f"setup: {e}")
        return results

    # Load vectors
    vectors, ids, metadata = generate_synthetic_data(n_vectors, dim, seed=42)
    t0 = time.time()
    adapter.load(vectors, ids, metadata)
    load_time = time.time() - t0

    # Build index
    t0 = time.time()
    adapter.build_index("hnsw", params={"m": 16, "ef_construction": 128})
    adapter.await_ready()
    results["index_build_time_ms"] = int((time.time() - t0) * 1000)

    # Generate queries
    rng = np.random.default_rng(123)
    queries = rng.random((n_queries, dim)).astype(np.float32).tolist()

    # Ground truth
    gt = brute_force_search(vectors, queries, 100, metric)

    # Run queries and measure latency
    latencies = []
    ann_results = []
    for qv in queries:
        t0 = time.time()
        try:
            res = adapter.search(qv, top_k=100)
        except Exception as e:
            results["errors"].append(f"search: {e}")
            continue
        latencies.append((time.time() - t0) * 1000)
        ann_results.append([r["id"] for r in res])

    if not latencies:
        return results

    results["latency_p50_ms"] = round(np.percentile(latencies, 50), 2)
    results["latency_p95_ms"] = round(np.percentile(latencies, 95), 2)
    results["latency_p99_ms"] = round(np.percentile(latencies, 99), 2)
    results["qps"] = round(n_queries / sum(latencies) * 1000, 2)

    results["recall_at_1"] = round(compute_recall_at_k(gt, ann_results, 1), 4)
    results["recall_at_10"] = round(compute_recall_at_k(gt, ann_results, 10), 4)
    results["recall_at_100"] = round(compute_recall_at_k(gt, ann_results, 100), 4)

    print(f"  Recall@1:  {results['recall_at_1']}")
    print(f"  Recall@10: {results['recall_at_10']}")
    print(f"  Recall@100: {results['recall_at_100']}")
    print(f"  Latency p50: {results['latency_p50_ms']}ms")
    print(f"  Latency p95: {results['latency_p95_ms']}ms")
    print(f"  Latency p99: {results['latency_p99_ms']}ms")
    print(f"  QPS: {results['qps']}")
    print(f"  Index build: {results['index_build_time_ms']}ms")

    return results


def main():
    parser = argparse.ArgumentParser(description="Almanac Benchmark Harness")
    parser.add_argument("--adapter", required=True, help="Adapter name (e.g., pinecone, qdrant, weaviate, milvus, pgvector)")
    parser.add_argument("--dataset", default="sift1m", help="Dataset name (sift1m, glove-100)")
    parser.add_argument("--metric", default="cosine", help="Distance metric (cosine, euclidean, dot_product)")
    parser.add_argument("--config", type=json.loads, default="{}", help="Adapter config as JSON dict")
    parser.add_argument("--smoke-only", action="store_true", help="Run only smoke gate")
    args = parser.parse_args()

    adapter = load_adapter(args.adapter, args.config)

    # Run smoke gate
    smoke_results = smoke_gate(adapter, dimension=384, metric=args.metric)

    if not smoke_results["passed"]:
        print("\nSmoke gate failed. Aborting benchmark.")
        adapter.teardown()
        sys.exit(1)

    if args.smoke_only:
        adapter.teardown()
        print("\nSmoke-only run complete.")
        sys.exit(0)

    # Run ANN benchmark
    ann_results = run_ann_benchmark(adapter, args.dataset, args.metric)

    # Teardown
    adapter.teardown()

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmarks" / "ann-benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_file = output_dir / f"{args.adapter}-{args.dataset}-{date_str}.json"

    full_results = {
        "meta": {
            "adapter": args.adapter,
            "dataset": args.dataset,
            "metric": args.metric,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "harness_version": "2026.06"
        },
        "smoke_gate": smoke_results,
        "ann_benchmark": ann_results,
        "ops_notes": adapter.get_ops_notes()
    }

    with open(output_file, "w") as f:
        json.dump(full_results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
