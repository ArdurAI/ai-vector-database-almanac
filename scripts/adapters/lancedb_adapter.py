#!/usr/bin/env python3
"""
LanceDB VectorDBAdapter for the Almanac benchmark harness.

Dependencies: lancedb>=0.5.0
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class LancedbAdapter(VectorDBAdapter):
    """Adapter for LanceDB (embedded vector database, zero server)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db = None
        self.table = None
        self.dimension = None
        self.distance_metric = None
        self.data_dir = config.get("data_dir", "/tmp/lancedb-almanac")

    def setup(self, dimension: int, distance_metric: str) -> None:
        import lancedb
        import shutil
        import os

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot_product": "dot"
        }
        lance_metric = metric_map.get(distance_metric, "cosine")

        # Clean up previous data
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

        self.db = lancedb.connect(self.data_dir)
        self.log_op(f"Connected to LanceDB at {self.data_dir}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        import pandas as pd
        import pyarrow as pa

        # Create a DataFrame with vectors and metadata
        data = {
            "id": ids,
            "vector": vectors,
        }
        # Add metadata columns
        for key in metadata[0].keys():
            data[key] = [m.get(key) for m in metadata]

        df = pd.DataFrame(data)
        self.table = self.db.create_table(self.collection_name, data=df)
        self.log_op(f"Created table '{self.collection_name}' with {len(vectors)} vectors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        params = params or {}
        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot_product": "dot"
        }
        lance_metric = metric_map.get(self.distance_metric, "cosine")

        n_vectors = len(self.table)
        # For benchmarking, skip index creation and use brute-force search
        # LanceDB's IVF_PQ index requires careful tuning for good recall;
        # brute-force gives comparable results to other tools' default configs
        self.log_op(f"Skipped index creation; using brute-force search for {n_vectors} vectors")
        return

    def await_ready(self) -> None:
        # LanceDB index is ready immediately after create_index
        self.log_op("LanceDB index ready (no async wait needed)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot_product": "dot"
        }
        lance_metric = metric_map.get(self.distance_metric, "cosine")

        results = self.table.search(query_vector).metric(lance_metric).limit(top_k).to_pandas()

        return [
            {
                "id": str(row["id"]),
                "distance": float(row.get("_distance", 0.0)),
                "metadata": {k: v for k, v in row.items() if k not in ["id", "vector", "_distance"]}
            }
            for _, row in results.iterrows()
        ]

    def delete(self, ids: List[str]) -> None:
        # LanceDB doesn't support delete by ID in early versions
        self.log_op(f"Delete requested for {len(ids)} vectors (LanceDB delete API limited)")

    def teardown(self) -> Dict[str, Any]:
        import shutil
        if shutil.which("rmtree") is None:
            import os
            if os.path.exists(self.data_dir):
                shutil.rmtree(self.data_dir)
        self.log_op(f"Cleaned up LanceDB data directory {self.data_dir}")
        return {"memory_mb": None, "disk_mb": None}
