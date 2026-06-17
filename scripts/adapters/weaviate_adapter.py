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
        # Weaviate requires class names to start with capital letter, alphanumeric only
        raw_name = self.collection_name
        sanitized = raw_name.replace("-", "").replace("_", "").capitalize()
        if not sanitized[0].isupper():
            sanitized = "Test" + sanitized
        self.collection_name = sanitized

    def setup(self, dimension: int, distance_metric: str) -> None:
        import weaviate
        from weaviate.classes.config import Configure, Property, DataType

        self.dimension = dimension
        self.distance_metric = distance_metric

        from weaviate.classes.config import VectorDistances
        metric_map = {
            "cosine": VectorDistances.COSINE,
            "euclidean": VectorDistances.L2_SQUARED,
            "dot_product": VectorDistances.DOT
        }
        weaviate_metric = metric_map.get(distance_metric, VectorDistances.COSINE)

        if self.use_docker:
            # Clean up any existing container with the same name
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
            time.sleep(1)
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "8080:8080",
                "-p", "50051:50051",
                "-e", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
                "-e", "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
                "semitechnologies/weaviate:latest"
            ], check=True, capture_output=True)
            # Poll REST endpoint until ready
            import urllib.request
            for _ in range(30):
                try:
                    urllib.request.urlopen("http://localhost:8080/v1/.well-known/ready", timeout=1)
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise TimeoutError("Weaviate did not become ready within 30 seconds")

        self.client = weaviate.connect_to_local(host="localhost", port=8080, skip_init_checks=True)

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

    def _to_weaviate_id(self, id_str: str) -> str:
        """Convert string IDs to valid UUIDs for Weaviate."""
        import uuid
        # Generate a deterministic UUID5 from the string ID
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        collection = self.client.collections.get(self.collection_name)
        from weaviate.classes.data import DataObject
        objects = [
            DataObject(
                properties={"__orig_id": id_, **meta},
                vector=vec,
                uuid=self._to_weaviate_id(id_)
            )
            for vec, id_, meta in zip(vectors, ids, metadata)
        ]
        # Batch insert in chunks to avoid overwhelming the server
        chunk_size = 2000
        for i in range(0, len(objects), chunk_size):
            chunk = objects[i:i + chunk_size]
            collection.data.insert_many(chunk)
        self.log_op(f"Upserted {len(vectors)} vectors in {len(objects) // chunk_size + (1 if len(objects) % chunk_size else 0)} chunks")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        collection = self.client.collections.get(self.collection_name)
        config = collection.config.get()
        metric = getattr(config.vector_index_config, 'distance', getattr(config.vector_index_config, 'metric', 'unknown'))
        self.log_op(f"Index config: type={config.vector_index_type}, metric={metric}")

    def await_ready(self) -> None:
        start = time.time()
        collection = self.client.collections.get(self.collection_name)
        # Weaviate auto-indexes; check batch errors
        if collection.batch.failed_objects:
            raise RuntimeError(f"Batch errors: {len(collection.batch.failed_objects)} objects failed")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (no async compaction needed)")

    def delete(self, ids: List[str]) -> None:
        collection = self.client.collections.get(self.collection_name)
        for id_ in ids:
            collection.data.delete_by_id(self._to_weaviate_id(id_))

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
            {"id": str(obj.properties.get("__orig_id", obj.uuid)), "distance": obj.metadata.distance, "metadata": {k: v for k, v in obj.properties.items() if not k.startswith("__")}}
            for obj in result.objects
        ]

    def teardown(self) -> Dict[str, Any]:
        if self.client:
            if self.client.collections.exists(self.collection_name):
                self.client.collections.delete(self.collection_name)
            self.log_op(f"Deleted collection '{self.collection_name}'")
            self.client.close()

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
