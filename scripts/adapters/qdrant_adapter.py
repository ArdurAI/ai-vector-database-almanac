#!/usr/bin/env python3
"""
Qdrant VectorDBAdapter for the Almanac benchmark harness.

Dependencies: qdrant-client>=1.7.0
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class QdrantAdapter(VectorDBAdapter):
    """Adapter for Qdrant (Docker single-node or remote)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:6333")
        self.client = None
        self.container_name = config.get("container_name", "qdrant-almanac")
        self.use_docker = config.get("use_docker", True)

    def setup(self, dimension: int, distance_metric: str) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID,
            "dot_product": Distance.DOT
        }
        qdrant_metric = metric_map.get(distance_metric, Distance.COSINE)

        if self.use_docker:
            # Start Qdrant in Docker
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "6333:6333", "-p", "6334:6334",
                "-v", f"{self.config.get('data_dir', '/tmp/qdrant')}:/qdrant/storage",
                "qdrant/qdrant:latest"
            ], check=True, capture_output=True)
            time.sleep(3)  # Wait for startup

        self.client = QdrantClient(url=self.url)

        # Delete collection if exists
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=dimension, distance=qdrant_metric)
        )
        self.log_op(f"Created collection '{self.collection_name}' with metric={distance_metric}, dim={dimension}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(id=id_, vector=vec, payload=meta)
            for vec, id_, meta in zip(vectors, ids, metadata)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        self.log_op(f"Upserted {len(points)} vectors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # Qdrant auto-builds HNSW on upsert. Log the effective config.
        info = self.client.get_collection(self.collection_name)
        hnsw_config = info.config.params.vectors.hnsw_config
        self.log_op(f"HNSW config: m={hnsw_config.m}, ef_construct={hnsw_config.ef_construct}, full_scan_threshold={hnsw_config.full_scan_threshold}")

    def await_ready(self) -> None:
        from qdrant_client.models import CollectionStatus
        start = time.time()
        while True:
            info = self.client.get_collection(self.collection_name)
            if info.status == CollectionStatus.GREEN:
                break
            if time.time() - start > 300:
                raise TimeoutError("Collection did not reach GREEN status within 5 minutes")
            time.sleep(0.5)
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (status=GREEN)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters
        )
        return [
            {"id": str(match.id), "distance": match.score, "metadata": match.payload}
            for match in result
        ]

    def delete(self, ids: List[str]) -> None:
        from qdrant_client.models import PointIdsList
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=ids)
        )

    def teardown(self) -> Dict[str, Any]:
        self.client.delete_collection(self.collection_name)
        self.log_op(f"Deleted collection '{self.collection_name}'")

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
