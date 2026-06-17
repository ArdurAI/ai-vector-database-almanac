#!/usr/bin/env python3
"""
Weaviate VectorDBAdapter for the Almanac benchmark harness.

Dependencies: weaviate-client>=4.0.0
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class WeaviateAdapter(VectorDBAdapter):
    """Adapter for Weaviate (Docker or remote)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "http://localhost:8080")
        self.client = None
        self.container_name = config.get("container_name", "weaviate-almanac")
        self.use_docker = config.get("use_docker", True)

    def setup(self, dimension: int, distance_metric: str) -> None:
        import weaviate
        from weaviate.classes.config import Configure, Property, DataType

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2-squared",
            "dot_product": "dot"
        }
        weaviate_metric = metric_map.get(distance_metric, "cosine")

        if self.use_docker:
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "8080:8080",
                "-e", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
                "-e", "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
                "semitechnologies/weaviate:latest"
            ], check=True, capture_output=True)
            time.sleep(5)

        self.client = weaviate.connect_to_local(host="localhost", port=8080)

        # Delete collection if exists
        if self.client.collections.exists(self.collection_name):
            self.client.collections.delete(self.collection_name)

        self.client.collections.create(
            name=self.collection_name,
            vectorizer_config=Configure.Vectorizer.none(),  # We provide pre-computed vectors
            properties=[
                Property(name="title", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
                Property(name="timestamp", data_type=DataType.DATE)
            ],
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=weaviate_metric
            )
        )
        self.log_op(f"Created collection '{self.collection_name}' with metric={weaviate_metric}, dim={dimension}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        collection = self.client.collections.get(self.collection_name)
        with collection.batch.dynamic() as batch:
            for vec, id_, meta in zip(vectors, ids, metadata):
                batch.add_object(
                    properties=meta,
                    vector=vec,
                    uuid=id_
                )
        self.log_op(f"Upserted {len(vectors)} vectors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        collection = self.client.collections.get(self.collection_name)
        config = collection.config.get()
        self.log_op(f"Index config: type={config.vector_index_type}, metric={config.vector_index_config.distance}")

    def await_ready(self) -> None:
        start = time.time()
        collection = self.client.collections.get(self.collection_name)
        # Weaviate auto-indexes; check batch errors
        if collection.batch.failed_objects:
            raise RuntimeError(f"Batch errors: {len(collection.batch.failed_objects)} objects failed")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (no async compaction needed)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        from weaviate.classes.query import Filter
        collection = self.client.collections.get(self.collection_name)

        weaviate_filter = None
        if filters:
            # Simple key-value equality filter
            for key, value in filters.items():
                weaviate_filter = Filter.by_property(key).equal(value)
                break  # Only single filter supported in this simple adapter

        result = collection.query.near_vector(
            near_vector=query_vector,
            limit=top_k,
            filters=weaviate_filter
        )
        return [
            {"id": str(obj.uuid), "distance": obj.metadata.distance, "metadata": obj.properties}
            for obj in result.objects
        ]

    def delete(self, ids: List[str]) -> None:
        collection = self.client.collections.get(self.collection_name)
        for id_ in ids:
            collection.data.delete_by_id(id_)

    def teardown(self) -> Dict[str, Any]:
        if self.client.collections.exists(self.collection_name):
            self.client.collections.delete(self.collection_name)
        self.log_op(f"Deleted collection '{self.collection_name}'")
        self.client.close()

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
