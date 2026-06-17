#!/usr/bin/env python3
"""
Milvus VectorDBAdapter for the Almanac benchmark harness.

Dependencies: pymilvus>=2.4.0
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class MilvusAdapter(VectorDBAdapter):
    """Adapter for Milvus (Docker standalone or remote)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", "19530")
        self.use_docker = config.get("use_docker", True)
        self.container_name = config.get("container_name", "milvus-standalone")

    def setup(self, dimension: int, distance_metric: str) -> None:
        from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "COSINE",
            "euclidean": "L2",
            "dot_product": "IP"
        }
        milvus_metric = metric_map.get(distance_metric, "COSINE")

        if self.use_docker:
            # Start Milvus standalone with etcd and minio via docker-compose is preferred
            # For simplicity, use Milvus Lite or single Docker container
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "19530:19530",
                "-p", "9091:9091",
                "milvusdb/milvus:latest",
                "milvus", "run", "standalone"
            ], check=True, capture_output=True)
            time.sleep(10)

        connections.connect(alias="default", host=self.host, port=self.port)

        # Drop existing collection
        if Collection(self.collection_name).exists():
            Collection(self.collection_name).drop()

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
        ]
        schema = CollectionSchema(fields, description="Almanac test collection")
        self.collection = Collection(name=self.collection_name, schema=schema)
        self.log_op(f"Created collection '{self.collection_name}' with metric={milvus_metric}, dim={dimension}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        entities = [
            ids,
            vectors,
            [m.get("title", "") for m in metadata],
            [m.get("category", "") for m in metadata]
        ]
        self.collection.insert(entities)
        self.log_op(f"Inserted {len(vectors)} vectors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        from pymilvus import Collection

        default_params = {"index_type": "HNSW", "metric_type": "COSINE", "params": {"M": 16, "efConstruction": 128}}
        if params:
            default_params.update(params)

        self.collection.create_index(field_name="vector", index_params=default_params)
        self.log_op(f"Built HNSW index: M={default_params['params']['M']}, efConstruction={default_params['params']['efConstruction']}")

    def await_ready(self) -> None:
        self.collection.load()
        start = time.time()
        # Milvus load() is async; wait for queryable state
        time.sleep(2)  # Simplified; production should poll
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (collection loaded)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
        expr = None
        if filters:
            parts = [f"{k} == '{v}'" for k, v in filters.items()]
            expr = " and ".join(parts)

        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["title", "category"]
        )
        output = []
        for hits in results:
            for hit in hits:
                output.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "metadata": {"title": hit.entity.get("title"), "category": hit.entity.get("category")}
                })
        return output

    def delete(self, ids: List[str]) -> None:
        expr = f"id in {ids}"
        self.collection.delete(expr)

    def teardown(self) -> Dict[str, Any]:
        self.collection.drop()
        self.log_op(f"Dropped collection '{self.collection_name}'")

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
