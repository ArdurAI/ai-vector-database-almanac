#!/usr/bin/env python3
"""
Milvus VectorDBAdapter for the Almanac benchmark harness.

Dependencies: pymilvus>=3.0.0, milvus-lite
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class MilvusAdapter(VectorDBAdapter):
    """Adapter for Milvus (Docker standalone, Milvus Lite, or remote)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 19530)
        self.use_docker = config.get("use_docker", True)
        self.use_lite = config.get("use_lite", False)
        self.container_name = config.get("container_name", "milvus-standalone")
        self.client = None
        # Milvus collection names can only contain numbers, letters and underscores
        raw_name = self.collection_name
        sanitized = raw_name.replace("-", "_").replace(" ", "_")
        if not sanitized[0].isalpha():
            sanitized = "test_" + sanitized
        self.collection_name = sanitized

    def setup(self, dimension: int, distance_metric: str) -> None:
        from pymilvus import MilvusClient, DataType

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "COSINE",
            "euclidean": "L2",
            "dot_product": "IP"
        }
        milvus_metric = metric_map.get(distance_metric, "COSINE")
        self.milvus_metric = milvus_metric

        if self.use_lite:
            db_path = self.config.get("db_path", "/tmp/milvus_almanac.db")
            self.client = MilvusClient(uri=db_path)
        else:
            if self.use_docker:
                subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
                time.sleep(1)
                subprocess.run([
                    "docker", "run", "-d", "--name", self.container_name,
                    "-p", "19530:19530",
                    "-p", "9091:9091",
                    "milvusdb/milvus:latest",
                    "milvus", "run", "standalone"
                ], check=True, capture_output=True)
                time.sleep(10)
            self.client = MilvusClient(uri=f"http://{self.host}:{self.port}")

        # Drop existing collection
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=dimension,
            metric_type=milvus_metric,
            id_type=DataType.VARCHAR,
            max_length=64
        )
        self.log_op(f"Created collection '{self.collection_name}' with metric={milvus_metric}, dim={dimension}")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        from pymilvus.milvus_client.index import IndexParams

        ip = IndexParams()
        # Milvus Lite only supports FLAT, IVF_FLAT, AUTOINDEX
        actual_index_type = "AUTOINDEX" if self.use_lite else "HNSW"
        ip.add_index(
            field_name="vector",
            index_type=actual_index_type,
            index_name="vector_idx",
            metric_type=self.milvus_metric,
        )

        self.client.create_index(collection_name=self.collection_name, index_params=ip)
        self.log_op(f"Built {actual_index_type} index: metric={self.milvus_metric}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        data = [
            {"id": id_, "vector": vec, **meta}
            for vec, id_, meta in zip(vectors, ids, metadata)
        ]
        self.client.insert(collection_name=self.collection_name, data=data)
        self.log_op(f"Inserted {len(vectors)} vectors")

    def await_ready(self) -> None:
        self.client.load_collection(self.collection_name)
        start = time.time()
        time.sleep(1)
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (collection loaded)")

    def delete(self, ids: List[str]) -> None:
        self.client.delete(collection_name=self.collection_name, ids=ids)

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        search_params = {"metric_type": self.milvus_metric, "params": {"ef": 64}}
        expr = None
        if filters:
            parts = [f"{k} == '{v}'" for k, v in filters.items()]
            expr = " and ".join(parts)

        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            filter=expr,
            output_fields=["*"]
        )
        output = []
        for hits in results:
            for hit in hits:
                output.append({
                    "id": hit["id"],
                    "distance": hit["distance"],
                    "metadata": {k: v for k, v in hit.items() if k not in ("id", "distance", "vector")}
                })
        return output

    def teardown(self) -> Dict[str, Any]:
        try:
            if self.client.has_collection(self.collection_name):
                self.client.drop_collection(self.collection_name)
                self.log_op(f"Dropped collection '{self.collection_name}'")
        except Exception:
            pass

        if self.use_docker and not self.use_lite:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
