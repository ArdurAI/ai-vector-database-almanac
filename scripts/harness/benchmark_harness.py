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
from typing import List, Dict, Any
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


def load_dataset(dataset_name: str, max_vectors: int = None, max_queries: int = None) -> dict:
    """Load a real dataset from benchmarks/data/."""
    data_dir = Path(__file__).parent.parent.parent / "benchmarks" / "data"
    
    file_map = {
        "sift1m": "sift_128_euclidean.npz",
        "sift-128-euclidean": "sift_128_euclidean.npz",
        "glove-100": "glove_100_angular.npz",
        "glove-100-angular": "glove_100_angular.npz",
    }
    
    filename = file_map.get(dataset_name, f"{dataset_name}.npz")
    filepath = data_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}. Available: {list(data_dir.glob('*.npz'))}")
    
    print(f"  Loading dataset from {filepath}...")
    data = np.load(filepath)
    
    train = data["train"]
    test = data["test"]
    neighbors = data["neighbors"]
    distance = str(data["distance"]) if "distance" in data else "euclidean"
    
    if max_vectors and max_vectors < len(train):
        train = train[:max_vectors]
    if max_queries and max_queries < len(test):
        test = test[:max_queries]
        neighbors = neighbors[:max_queries]
    
    print(f"  Loaded: train={train.shape}, test={test.shape}, neighbors={neighbors.shape}, distance={distance}")
    
    return {
        "train": train,
        "test": test,
        "neighbors": neighbors,
        "distance": distance,
    }


def compute_recall_at_k(ground_truth: List[List[int]], results: List[List[str]], k: int) -> float:
    """Compute recall@k against brute-force ground truth.
    
    ground_truth: list of lists of integer indices (from .npz neighbors)
    results: list of lists of string IDs (from adapter search)
    """
    recalls = []
    for gt, res in zip(ground_truth, results):
        gt_set = set(gt[:k])
        res_ints = set()
        for r in res[:k]:
            if isinstance(r, str) and r.startswith("vec-"):
                try:
                    res_ints.add(int(r.split("-")[1]))
                except ValueError:
                    pass
            elif isinstance(r, int):
                res_ints.add(r)
            else:
                try:
                    res_ints.add(int(r))
                except (ValueError, TypeError):
                    pass
        if gt_set:
            recalls.append(len(gt_set & res_ints) / len(gt_set))
    return sum(recalls) / len(recalls) if recalls else 0.0


def brute_force_search(vectors: List[List[float]], queries: List[List[float]], top_k: int, metric: str) -> List[List[str]]:
    """Brute-force exact search for ground truth."""
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

    t0 = time.time()
    try:
        adapter.setup(dimension=dimension, distance_metric=metric)
        results["setup_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Setup: {results['setup_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"setup failed: {e}")
        print(f"  FAILED: {e}")
        return results

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

    query_vectors = vectors[:10]
    try:
        ann_results = []
        for qv in query_vectors:
            res = adapter.search(qv, top_k=10)
            ann_results.append([r["id"] for r in res])

        gt = brute_force_search(vectors, query_vectors, 10, metric)
        recall = compute_recall_at_k([[int(x.split("-")[1]) for x in row] for row in gt], ann_results, 10)
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


def run_ann_benchmark(adapter: VectorDBAdapter, dataset_name: str, metric: str, max_vectors: int = None, max_queries: int = None) -> dict:
    """
    Run ANN-Benchmarks on a real dataset loaded from benchmarks/data/.
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
        "load_time_ms": 0,
        "qps": 0.0,
        "errors": []
    }

    try:
        ds = load_dataset(dataset_name, max_vectors=max_vectors, max_queries=max_queries)
    except Exception as e:
        results["errors"].append(f"dataset load: {e}")
        print(f"  FAILED: {e}")
        return results

    dim = ds["train"].shape[1]
    n_vectors = len(ds["train"])
    n_queries = len(ds["test"])
    
    # Use dataset's native distance if not overridden
    dataset_metric = ds["distance"]
    if metric == "cosine" and dataset_metric == "angular":
        metric = "cosine"  # angular = cosine distance in ANN-benchmarks
    elif metric == "euclidean" and dataset_metric == "euclidean":
        metric = "euclidean"

    # Setup
    try:
        adapter.setup(dimension=dim, distance_metric=metric)
    except Exception as e:
        results["errors"].append(f"setup: {e}")
        return results

    # Load vectors
    ids = [f"vec-{i:07d}" for i in range(n_vectors)]
    metadata = [{"index": i} for i in range(n_vectors)]
    vectors = ds["train"].astype(np.float32).tolist()
    
    t0 = time.time()
    try:
        adapter.load(vectors, ids, metadata)
        results["load_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Load {n_vectors} vectors: {results['load_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"load: {e}")
        print(f"  FAILED: {e}")
        return results

    # Build index
    t0 = time.time()
    try:
        adapter.build_index("hnsw", params={"m": 16, "ef_construction": 128})
        adapter.await_ready()
        results["index_build_time_ms"] = int((time.time() - t0) * 1000)
        print(f"  Build index: {results['index_build_time_ms']}ms")
    except Exception as e:
        results["errors"].append(f"build_index: {e}")
        print(f"  FAILED: {e}")
        return results

    # Run queries and measure latency
    queries = ds["test"].astype(np.float32).tolist()
    ground_truth = ds["neighbors"].astype(np.int32).tolist()
    
    latencies = []
    ann_results = []
    for i, qv in enumerate(queries):
        t0 = time.time()
        try:
            res = adapter.search(qv, top_k=100)
        except Exception as e:
            results["errors"].append(f"search q{i}: {e}")
            continue
        latencies.append((time.time() - t0) * 1000)
        ann_results.append([r["id"] for r in res])
        if (i + 1) % 1000 == 0 or (i + 1) == len(queries):
            print(f"  Queries {i+1}/{len(queries)}...")

    if not latencies:
        return results

    results["latency_p50_ms"] = round(np.percentile(latencies, 50), 2)
    results["latency_p95_ms"] = round(np.percentile(latencies, 95), 2)
    results["latency_p99_ms"] = round(np.percentile(latencies, 99), 2)
    results["qps"] = round(len(queries) / sum(latencies) * 1000, 2)

    results["recall_at_1"] = round(compute_recall_at_k(ground_truth, ann_results, 1), 4)
    results["recall_at_10"] = round(compute_recall_at_k(ground_truth, ann_results, 10), 4)
    results["recall_at_100"] = round(compute_recall_at_k(ground_truth, ann_results, 100), 4)

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
    parser.add_argument("--max-vectors", type=int, default=None, help="Limit number of vectors to load")
    parser.add_argument("--max-queries", type=int, default=None, help="Limit number of queries to run")
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
    ann_results = run_ann_benchmark(adapter, args.dataset, args.metric, max_vectors=args.max_vectors, max_queries=args.max_queries)

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
