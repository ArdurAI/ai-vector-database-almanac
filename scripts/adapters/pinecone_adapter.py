#!/usr/bin/env python3
"""
Pinecone VectorDBAdapter for the Almanac benchmark harness.

Dependencies: pinecone-client>=3.0.0
"""

import time
import os
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class PineconeAdapter(VectorDBAdapter):
    """Adapter for Pinecone Serverless and pod-based indexes."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", os.environ.get("PINECONE_API_KEY"))
        self.index_name = config.get("index_name", "almanac-test")
        self.pc = None
        self.index = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        from pinecone import Pinecone, ServerlessSpec

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosine",
            "euclidean": "euclidean",
            "dot_product": "dotproduct"
        }
        pinecone_metric = metric_map.get(distance_metric, "cosine")

        self.pc = Pinecone(api_key=self.api_key)

        # Delete existing index if it exists
        if self.index_name in [idx.name for idx in self.pc.list_indexes()]:
            self.pc.delete_index(self.index_name)
            time.sleep(2)  # Wait for deletion

        self.pc.create_index(
            name=self.index_name,
            dimension=dimension,
            metric=pinecone_metric,
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        self.log_op(f"Created index '{self.index_name}' with metric={pinecone_metric}, dim={dimension}")

        # Wait for index to be ready
        while not self.pc.describe_index(self.index_name).status["ready"]:
            time.sleep(1)

        self.index = self.pc.Index(self.index_name)

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        records = []
        for vec, id_, meta in zip(vectors, ids, metadata):
            records.append({"id": id_, "values": vec, "metadata": meta})

        # Batch upsert in chunks of 100
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace="")
        self.log_op(f"Upserted {len(records)} vectors in batches of {batch_size}")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # Pinecone serverless auto-builds index on upsert
        # We log the index configuration
        index_info = self.pc.describe_index(self.index_name)
        self.log_op(f"Index config: metric={index_info.metric}, dimension={index_info.dimension}")
        # No explicit build step for Pinecone serverless

    def await_ready(self) -> None:
        # Pinecone serverless: check stats reflect all vectors
        start = time.time()
        while True:
            stats = self.index.describe_index_stats()
            if stats.total_vector_count >= len(self.config.get("expected_count", 0)):
                break
            if time.time() - start > 300:  # 5 min timeout
                raise TimeoutError("Index did not become ready within 5 minutes")
            time.sleep(0.5)
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        result = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )
        return [
            {"id": match.id, "distance": match.score, "metadata": match.metadata}
            for match in result.matches
        ]

    def delete(self, ids: List[str]) -> None:
        self.index.delete(ids=ids, namespace="")

    def teardown(self) -> Dict[str, Any]:
        if self.pc and self.index_name:
            self.pc.delete_index(self.index_name)
        self.log_op(f"Deleted index '{self.index_name}'")
        return {"memory_mb": None, "disk_mb": None}  # Pinecone is opaque
