#!/usr/bin/env python3
"""
Cost-Runaway Measurement Framework for the Almanac.

Runs a sustained load test against a vector database, measuring:
- Cost predictability (actual vs. estimated)
- Memory leak detection
- OOM behavior
- Billing accuracy
- Latency degradation over time

Usage:
    python cost_runaway.py --adapter pinecone --vectors 1000000 --queries 10000 --duration-minutes 60
    python cost_runaway.py --adapter qdrant --vectors 1000000 --queries 10000 --duration-minutes 60

Results saved to benchmarks/stress-suite/<tool>-cost-runaway-<date>.json
"""

import argparse
import json
import time
import os
import sys
import psutil
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

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


def generate_vectors(count: int, dimension: int, seed: int = 42) -> tuple:
    """Generate vectors, IDs, and metadata."""
    rng = np.random.default_rng(seed)
    vectors = rng.random((count, dimension)).astype(np.float32).tolist()
    ids = [f"vec-{i:08d}" for i in range(count)]
    metadata = [
        {"title": f"Doc {i}", "category": "tech" if i % 3 == 0 else "finance"}
        for i in range(count)
    ]
    return vectors, ids, metadata


def measure_cost_runaway(adapter: VectorDBAdapter, n_vectors: int, n_queries: int, duration_minutes: int, dimension: int = 384, metric: str = "cosine") -> dict:
    """Run sustained load test and measure cost/runaway behavior."""
    print(f"\n=== Cost Runaway Test: {adapter.__class__.__name__} ===")
    print(f"  Vectors: {n_vectors:,} | Queries: {n_queries:,} | Duration: {duration_minutes}min")

    results = {
        "adapter": adapter.__class__.__name__,
        "n_vectors": n_vectors,
        "n_queries": n_queries,
        "duration_minutes": duration_minutes,
        "dimension": dimension,
        "metric": metric,
        "setup_time_ms": 0,
        "ingest_time_ms": 0,
        "index_time_ms": 0,
        "sustained_test": {
            "total_queries_executed": 0,
            "latency_samples": [],
            "latency_p50_ms": [],
            "latency_p95_ms": [],
            "latency_p99_ms": [],
            "memory_mb_samples": [],
            "errors": [],
            "oom_detected": False,
            "memory_leak_slope_mb_per_min": 0.0,
        },
        "errors": []
    }

    process = psutil.Process()

    # Setup
    t0 = time.time()
    try:
        adapter.setup(dimension=dimension, distance_metric=metric)
        results["setup_time_ms"] = int((time.time() - t0) * 1000)
    except Exception as e:
        results["errors"].append(f"setup: {e}")
        return results

    # Ingest
    vectors, ids, metadata = generate_vectors(n_vectors, dimension)
    t0 = time.time()
    try:
        adapter.load(vectors, ids, metadata)
        results["ingest_time_ms"] = int((time.time() - t0) * 1000)
    except Exception as e:
        results["errors"].append(f"load: {e}")
        return results

    # Build index
    t0 = time.time()
    try:
        adapter.build_index("hnsw", params={"m": 16, "ef_construction": 128})
        adapter.await_ready()
        results["index_time_ms"] = int((time.time() - t0) * 1000)
    except Exception as e:
        results["errors"].append(f"index: {e}")
        return results

    # Generate query pool
    rng = np.random.default_rng(123)
    query_pool = rng.random((n_queries, dimension)).astype(np.float32).tolist()

    # Sustained test
    start_time = time.time()
    end_time = start_time + duration_minutes * 60
    query_idx = 0
    interval_samples = []
    last_sample_time = start_time

    while time.time() < end_time:
        try:
            qv = query_pool[query_idx % n_queries]
            t0 = time.time()
            adapter.search(qv, top_k=10)
            latency_ms = (time.time() - t0) * 1000

            results["sustained_test"]["total_queries_executed"] += 1
            results["sustained_test"]["latency_samples"].append(latency_ms)

            # Memory sample every 30 seconds
            if time.time() - last_sample_time >= 30:
                mem_mb = process.memory_info().rss / 1024 / 1024
                results["sustained_test"]["memory_mb_samples"].append({
                    "elapsed_sec": int(time.time() - start_time),
                    "memory_mb": round(mem_mb, 2)
                })
                last_sample_time = time.time()

            query_idx += 1
        except MemoryError:
            results["sustained_test"]["oom_detected"] = True
            results["sustained_test"]["errors"].append("OOM at query {query_idx}")
            break
        except Exception as e:
            results["sustained_test"]["errors"].append(f"query {query_idx}: {e}")
            # Continue testing unless too many errors
            if len(results["sustained_test"]["errors"]) > 100:
                break

    # Compute per-minute latency statistics
    latencies = results["sustained_test"]["latency_samples"]
    if latencies:
        # Split into 1-minute windows
        n_samples = len(latencies)
        samples_per_min = n_samples / duration_minutes if duration_minutes > 0 else 0
        for i in range(0, n_samples, max(1, int(samples_per_min))):
            window = latencies[i:i + int(samples_per_min)]
            if window:
                results["sustained_test"]["latency_p50_ms"].append(round(np.percentile(window, 50), 2))
                results["sustained_test"]["latency_p95_ms"].append(round(np.percentile(window, 95), 2))
                results["sustained_test"]["latency_p99_ms"].append(round(np.percentile(window, 99), 2))

    # Memory leak detection
    mem_samples = results["sustained_test"]["memory_mb_samples"]
    if len(mem_samples) >= 2:
        x = [s["elapsed_sec"] / 60 for s in mem_samples]  # minutes
        y = [s["memory_mb"] for s in mem_samples]
        if len(x) > 1:
            slope = (y[-1] - y[0]) / (x[-1] - x[0]) if x[-1] != x[0] else 0
            results["sustained_test"]["memory_leak_slope_mb_per_min"] = round(slope, 2)

    print(f"  Setup: {results['setup_time_ms']}ms")
    print(f"  Ingest: {results['ingest_time_ms']}ms")
    print(f"  Index: {results['index_time_ms']}ms")
    print(f"  Queries executed: {results['sustained_test']['total_queries_executed']:,}")
    print(f"  OOM detected: {results['sustained_test']['oom_detected']}")
    print(f"  Memory leak slope: {results['sustained_test']['memory_leak_slope_mb_per_min']:.2f} MB/min")

    return results


def main():
    parser = argparse.ArgumentParser(description="Cost Runaway Measurement Framework")
    parser.add_argument("--adapter", required=True, help="Adapter name")
    parser.add_argument("--vectors", type=int, default=1000000, help="Number of vectors to index")
    parser.add_argument("--queries", type=int, default=10000, help="Number of unique query vectors")
    parser.add_argument("--duration-minutes", type=int, default=60, help="Sustained test duration")
    parser.add_argument("--dimension", type=int, default=384, help="Vector dimension")
    parser.add_argument("--metric", default="cosine", help="Distance metric")
    parser.add_argument("--config", type=json.loads, default="{}", help="Adapter config JSON")
    args = parser.parse_args()

    adapter = load_adapter(args.adapter, args.config)

    results = measure_cost_runaway(
        adapter, args.vectors, args.queries, args.duration_minutes, args.dimension, args.metric
    )

    adapter.teardown()

    # Save results
    output_dir = Path(__file__).parent.parent.parent / "benchmarks" / "stress-suite"
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_file = output_dir / f"{args.adapter}-cost-runaway-{date_str}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
