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
            # Clean up any existing container with the same name
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
            time.sleep(1)
            # Start Qdrant in Docker
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "6333:6333", "-p", "6334:6334",
                "-v", f"{self.config.get('data_dir', '/tmp/qdrant')}:/qdrant/storage",
                "qdrant/qdrant:latest"
            ], check=True, capture_output=True)
            time.sleep(3)  # Wait for startup

        self.client = QdrantClient(url=self.url, grpc_port=6334, check_compatibility=False, timeout=30)

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

    def _to_qdrant_id(self, id_str: str) -> int:
        """Convert string IDs (e.g., 'vec-0000') to integers for Qdrant."""
        try:
            # Extract numeric part after last hyphen or use hash
            if "-" in id_str:
                return int(id_str.split("-")[-1])
            return int(id_str)
        except ValueError:
            # Fallback: use hash (must fit in unsigned 64-bit)
            return hash(id_str) & 0xFFFFFFFF

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        from qdrant_client.models import PointStruct

        int_ids = [self._to_qdrant_id(id_) for id_ in ids]
        points = [
            PointStruct(id=id_int, vector=vec, payload={"__orig_id": id_str, **meta})
            for vec, id_int, id_str, meta in zip(vectors, int_ids, ids, metadata)
        ]
        # Batch upsert to stay within Qdrant's limits and avoid connection timeouts
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(collection_name=self.collection_name, points=batch)
            time.sleep(0.05)  # Small delay to avoid overwhelming the server
        self.log_op(f"Upserted {len(points)} vectors in {len(points) // batch_size + (1 if len(points) % batch_size else 0)} batches")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # Qdrant auto-builds HNSW on upsert. Log the effective config.
        info = self.client.get_collection(self.collection_name)
        vectors_config = info.config.params.vectors
        if vectors_config and hasattr(vectors_config, 'hnsw_config') and vectors_config.hnsw_config:
            hnsw = vectors_config.hnsw_config
            self.log_op(f"HNSW config: m={hnsw.m}, ef_construct={hnsw.ef_construct}, full_scan_threshold={hnsw.full_scan_threshold}")
        else:
            self.log_op("HNSW config: not yet available (auto-builds on data insert)")

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
        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=filters
        )
        return [
            {"id": str(point.payload.get("__orig_id", point.id)), "distance": point.score, "metadata": {k: v for k, v in point.payload.items() if not k.startswith("__")}}
            for point in result.points
        ]

    def delete(self, ids: List[str]) -> None:
        from qdrant_client.models import PointIdsList
        int_ids = [self._to_qdrant_id(id_) for id_ in ids]
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=int_ids)
        )

    def teardown(self) -> Dict[str, Any]:
        self.client.delete_collection(self.collection_name)
        self.log_op(f"Deleted collection '{self.collection_name}'")

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
