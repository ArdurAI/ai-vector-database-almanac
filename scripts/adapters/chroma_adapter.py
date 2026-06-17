#!/usr/bin/env python3
"""
Chroma VectorDBAdapter for the Almanac benchmark harness.

Dependencies: chromadb>=0.5.0
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class ChromaAdapter(VectorDBAdapter):
    """Adapter for Chroma (embedded vector database, in-process)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.collection = None
        self.dimension = None
        self.distance_metric = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        import chromadb
        from chromadb.config import Settings

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot_product": "ip"
        }
        chroma_metric = metric_map.get(distance_metric, "cosine")

        # Use ephemeral in-memory client for benchmarking
        self.client = chromadb.Client()

        # Delete collection if exists

        # Delete collection if exists
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": chroma_metric}
        )
        self.log_op(f"Created collection '{self.collection_name}' with metric={chroma_metric}, dim={dimension}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        # Chroma expects list of dicts for metadata
        batch_size = 1000
        for i in range(0, len(vectors), batch_size):
            end = min(i + batch_size, len(vectors))
            self.collection.add(
                embeddings=vectors[i:end],
                ids=ids[i:end],
                metadatas=metadata[i:end]
            )
        self.log_op(f"Added {len(vectors)} vectors to Chroma")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # Chroma auto-builds HNSW on add. No explicit build needed.
        params = params or {}
        self.log_op(f"Chroma HNSW index auto-built (m={params.get('m', 16)}, ef_construction={params.get('ef_construction', 100)})")

    def await_ready(self) -> None:
        # Chroma is ready immediately after add
        self.log_op("Chroma collection ready (no async wait needed)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        result = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filters
        )

        results = []
        for i in range(len(result["ids"][0])):
            results.append({
                "id": result["ids"][0][i],
                "distance": result["distances"][0][i] if result["distances"] else 0.0,
                "metadata": result["metadatas"][0][i] if result["metadatas"] else {}
            })
        return results

    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)

    def teardown(self) -> Dict[str, Any]:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.log_op(f"Deleted collection '{self.collection_name}'")
        return {"memory_mb": None, "disk_mb": None}
