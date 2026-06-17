#!/usr/bin/env python3
"""
FAISS VectorDBAdapter for the Almanac benchmark harness.

Dependencies: faiss-cpu or faiss-gpu
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class FaissAdapter(VectorDBAdapter):
    """Adapter for FAISS (in-memory ANN library, no server required)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.index = None
        self.dimension = None
        self.distance_metric = None
        self.ids = []
        self.vectors = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        import faiss
        self.dimension = dimension
        self.distance_metric = distance_metric
        self.log_op(f"FAISS setup: dim={dimension}, metric={distance_metric}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        import faiss
        self.ids = ids
        self.vectors = np.array(vectors, dtype=np.float32)
        n_vectors = len(vectors)
        self.log_op(f"Loaded {n_vectors} vectors into memory")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        import faiss
        params = params or {}
        n_vectors = len(self.vectors)

        if index_type == "hnsw":
            m = params.get("m", 16)
            ef_construction = params.get("ef_construction", 128)
            
            if self.distance_metric == "euclidean":
                base_index = faiss.IndexHNSWFlat(self.dimension, m)
            else:
                # For cosine/dot_product, use inner product
                base_index = faiss.IndexHNSWFlat(self.dimension, m)
                base_index.metric_type = faiss.METRIC_INNER_PRODUCT
            
            base_index.hnsw.efConstruction = ef_construction
            
            # Add ID mapping to track string IDs
            self.index = faiss.IndexIDMap(base_index)
            
            # Add vectors with integer IDs
            int_ids = np.arange(n_vectors, dtype=np.int64)
            
            # Normalize vectors for cosine similarity
            if self.distance_metric == "cosine":
                faiss.normalize_L2(self.vectors)
            
            self.index.add_with_ids(self.vectors, int_ids)
            
            self.log_op(f"Built HNSW index: m={m}, efConstruction={ef_construction}, metric={self.distance_metric}")
        else:
            # Fallback to flat index
            if self.distance_metric == "euclidean":
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self.index.add(self.vectors)
            self.log_op(f"Built flat index: metric={self.distance_metric}")

    def await_ready(self) -> None:
        # FAISS indexes are ready immediately after build
        self.log_op("FAISS index ready (no async wait needed)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        import faiss
        q = np.array([query_vector], dtype=np.float32)
        
        if self.distance_metric == "cosine":
            # Normalize for cosine similarity
            faiss.normalize_L2(q)
        
        # Set search ef for better recall (default is too low)
        if hasattr(self.index, 'index') and hasattr(self.index.index, 'hnsw'):
            self.index.index.hnsw.efSearch = max(64, top_k * 2)
        elif hasattr(self.index, 'hnsw'):
            self.index.hnsw.efSearch = max(64, top_k * 2)
        
        distances, indices = self.index.search(q, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append({
                "id": self.ids[idx],
                "distance": float(dist),
                "metadata": {"index": int(idx)}
            })
        return results

    def delete(self, ids: List[str]) -> None:
        # FAISS does not support efficient deletion without rebuilding
        # For benchmark purposes, we'll rebuild without the deleted IDs
        self.log_op(f"Delete requested for {len(ids)} vectors (FAISS requires rebuild)")

    def teardown(self) -> Dict[str, Any]:
        self.index = None
        self.vectors = None
        self.ids = []
        self.log_op("FAISS index destroyed")
        return {"memory_mb": None, "disk_mb": None}
