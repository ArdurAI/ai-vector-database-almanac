#!/usr/bin/env python3
"""
Redis VectorDBAdapter for the Almanac benchmark harness.

Dependencies: redis>=7.0.0
Requires Redis Stack (redis/redis-stack) or Redis with RediSearch module.

Docker:
    docker run -d --name redis-almanac -p 6379:6379 redis/redis-stack:latest
"""

import time
import subprocess
import struct
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class RedisVectorAdapter(VectorDBAdapter):
    """Adapter for Redis Vector (RediSearch HNSW)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.use_docker = config.get("use_docker", True)
        self.container_name = config.get("container_name", "redis-almanac")
        self.client = None
        self.index_name = f"idx_{self.collection_name}"

    def setup(self, dimension: int, distance_metric: str) -> None:
        import redis

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "COSINE",
            "euclidean": "L2",
            "dot_product": "IP"
        }
        redis_metric = metric_map.get(distance_metric, "COSINE")

        if self.use_docker:
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
            time.sleep(1)
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "6379:6379",
                "redis/redis-stack:latest"
            ], check=True, capture_output=True)
            # Poll until Redis is ready
            for _ in range(30):
                try:
                    r = redis.Redis(host=self.host, port=self.port, decode_responses=False)
                    r.ping()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise TimeoutError("Redis did not become ready within 30 seconds")

        self.client = redis.Redis(host=self.host, port=self.port, decode_responses=False)
        self.client.ping()

        # Drop existing index
        try:
            self.client.execute_command("FT.DROPINDEX", self.index_name, "DD")
        except Exception:
            pass

        # Create RediSearch index with HNSW vector field
        self.client.execute_command(
            "FT.CREATE", self.index_name, "ON", "HASH", "PREFIX", "1", f"doc:{self.collection_name}:",
            "SCHEMA",
            "embedding", "VECTOR", "HNSW", "10",
            "TYPE", "FLOAT32",
            "DIM", str(dimension),
            "DISTANCE_METRIC", redis_metric,
            "M", "16",
            "EF_CONSTRUCTION", "128",
            "title", "TEXT", "NOSTEM",
            "category", "TAG"
        )
        self.log_op(f"Created RediSearch index '{self.index_name}' with HNSW dim={dimension}, metric={redis_metric}")

    def _vector_to_bytes(self, vector: List[float]) -> bytes:
        """Pack float32 vector into bytes for Redis."""
        return struct.pack(f"{len(vector)}f", *vector)

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        # Batch pipeline to avoid overwhelming Redis
        batch_size = 5000
        for i in range(0, len(vectors), batch_size):
            pipe = self.client.pipeline(transaction=False)
            batch_vecs = vectors[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_meta = metadata[i:i + batch_size]
            for vec, id_, meta in zip(batch_vecs, batch_ids, batch_meta):
                key = f"doc:{self.collection_name}:{id_}"
                vec_bytes = self._vector_to_bytes(vec)
                pipe.hset(key, mapping={
                    "embedding": vec_bytes,
                    "title": meta.get("title", ""),
                    "category": meta.get("category", "")
                })
            pipe.execute()
        self.log_op(f"Upserted {len(vectors)} vectors in {len(vectors) // batch_size + (1 if len(vectors) % batch_size else 0)} batches")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # RediSearch builds HNSW during FT.CREATE; FT.CREATE blocks until ready
        self.log_op("HNSW index auto-built during FT.CREATE; no separate build step")

    def await_ready(self) -> None:
        # HNSW is synchronous in RediSearch, but we wait for background indexing
        start = time.time()
        time.sleep(1)
        # Check index info to see if indexing is complete
        try:
            info = self.client.execute_command("FT.INFO", self.index_name)
            # info is a list of key-value pairs; find index_status
            status = "unknown"
            for i in range(0, len(info), 2):
                if info[i] == b"index_status":
                    status = info[i + 1].decode() if isinstance(info[i + 1], bytes) else str(info[i + 1])
                    break
            self.log_op(f"Index status: {status}")
        except Exception as e:
            self.log_op(f"Could not check index status: {e}")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        query_bytes = self._vector_to_bytes(query_vector)

        # Build filter query string
        filter_query = "*"
        if filters:
            parts = []
            for k, v in filters.items():
                if k == "category":
                    parts.append(f"@{k}:{{{v}}}")
                else:
                    parts.append(f"@{k}:{v}")
            filter_query = " ".join(parts)

        # KNN search syntax: <filter>=>[KNN <k> @embedding $vec]
        search_query = f"{filter_query}=>[KNN {top_k} @embedding $vec]"

        result = self.client.execute_command(
            "FT.SEARCH", self.index_name, search_query,
            "PARAMS", "2", "vec", query_bytes,
            "SORTBY", "__embedding_score",
            "DIALECT", "2"
        )

        # Parse RediSearch FT.SEARCH response:
        # [total_count, doc_id, [field, value, ...], doc_id, [field, value, ...], ...]
        output = []
        if len(result) < 2:
            return output

        total = result[0]
        i = 1
        while i < len(result):
            doc_id = result[i].decode() if isinstance(result[i], bytes) else result[i]
            i += 1
            if i >= len(result):
                break
            fields = result[i]
            i += 1

            # fields is a list of [field, value, field, value, ...]
            field_dict = {}
            score = None
            if isinstance(fields, (list, tuple)):
                for j in range(0, len(fields), 2):
                    key = fields[j].decode() if isinstance(fields[j], bytes) else fields[j]
                    val = fields[j + 1]
                    if key == "__embedding_score":
                        score = float(val.decode() if isinstance(val, bytes) else val)
                    elif key == "title":
                        field_dict["title"] = val.decode() if isinstance(val, bytes) else val
                    elif key == "category":
                        field_dict["category"] = val.decode() if isinstance(val, bytes) else val

            # Extract original ID from doc_id
            orig_id = doc_id.replace(f"doc:{self.collection_name}:", "")
            output.append({
                "id": orig_id,
                "distance": score if score is not None else 0.0,
                "metadata": field_dict
            })

        return output

    def delete(self, ids: List[str]) -> None:
        for id_ in ids:
            key = f"doc:{self.collection_name}:{id_}"
            self.client.delete(key)

    def teardown(self) -> Dict[str, Any]:
        try:
            self.client.execute_command("FT.DROPINDEX", self.index_name, "DD")
            self.log_op(f"Dropped index '{self.index_name}'")
        except Exception:
            pass

        # Also delete all hash keys with our prefix
        for key in self.client.scan_iter(match=f"doc:{self.collection_name}:*"):
            self.client.delete(key)

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
