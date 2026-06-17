#!/usr/bin/env python3
"""
OpenSearch VectorDBAdapter for the Almanac benchmark harness.

Dependencies: opensearch-py>=3.0.0

Docker:
    docker run -d --name opensearch-almanac -p 9200:9200 -e "discovery.type=single-node" -e "plugins.security.disabled=true" opensearchproject/opensearch:2.18.0
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class OpensearchAdapter(VectorDBAdapter):
    """Adapter for OpenSearch 2.x with k-NN plugin."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 9200)
        self.use_docker = config.get("use_docker", True)
        self.container_name = config.get("container_name", "opensearch-almanac")
        self.client = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        from opensearchpy import OpenSearch

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosinesimil",
            "euclidean": "l2",
            "dot_product": "innerproduct"
        }
        os_metric = metric_map.get(distance_metric, "cosinesimil")

        if self.use_docker:
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
            time.sleep(1)
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "9200:9200",
                "-e", "discovery.type=single-node",
                "-e", "plugins.security.disabled=true",
                "-e", "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m",
                "opensearchproject/opensearch:2.18.0"
            ], check=True, capture_output=True)
            # Poll until OpenSearch is ready
            for _ in range(120):
                try:
                    os_client = OpenSearch([f"http://{self.host}:{self.port}"])
                    if os_client.ping():
                        break
                except Exception:
                    time.sleep(1)
            else:
                raise TimeoutError("OpenSearch did not become ready within 120 seconds")

        self.client = OpenSearch([f"http://{self.host}:{self.port}"])
        self.client.ping()

        # Delete index if exists
        try:
            self.client.indices.delete(index=self.collection_name)
        except Exception:
            pass

        # Create index with k-NN mapping
        self.client.indices.create(
            index=self.collection_name,
            body={
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    },
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "knn_vector",
                            "dimension": dimension,
                            "method": {
                                "name": "hnsw",
                                "engine": "nmslib",
                                "space_type": os_metric,
                                "parameters": {
                                    "m": 16,
                                    "ef_construction": 128
                                }
                            }
                        },
                        "title": {"type": "text"},
                        "category": {"type": "keyword"}
                    }
                }
            }
        )
        self.log_op(f"Created OpenSearch index '{self.collection_name}' with HNSW dim={dimension}, metric={os_metric}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        from opensearchpy.helpers import bulk

        actions = []
        for vec, id_, meta in zip(vectors, ids, metadata):
            actions.append({
                "_index": self.collection_name,
                "_id": id_,
                "_source": {
                    "vector": vec,
                    "title": meta.get("title", ""),
                    "category": meta.get("category", "")
                }
            })

        success, errors = bulk(self.client, actions, refresh=False)
        self.log_op(f"Bulk indexed {success} vectors, {len(errors)} errors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        # OpenSearch k-NN index is built during refresh
        self.client.indices.refresh(index=self.collection_name)
        self.log_op("Refreshed index (k-NN HNSW auto-built during ingestion)")

    def await_ready(self) -> None:
        start = time.time()
        self.client.indices.refresh(index=self.collection_name)
        self.client.cluster.health(wait_for_status="green", timeout="30s")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (index green)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        knn_body = {
            "vector": {
                "vector": query_vector,
                "k": top_k
            }
        }

        # Add filter if provided
        if filters:
            must_clauses = []
            for k, v in filters.items():
                must_clauses.append({"term": {k: v}})
            if must_clauses:
                knn_body["filter"] = {"bool": {"must": must_clauses}}

        result = self.client.search(
            index=self.collection_name,
            body={
                "size": top_k,
                "query": {
                    "knn": knn_body
                },
                "fields": ["title", "category"],
                "_source": False
            }
        )

        output = []
        for hit in result["hits"]["hits"]:
            fields = hit.get("fields", {})
            output.append({
                "id": hit["_id"],
                "distance": hit["_score"],
                "metadata": {
                    "title": fields.get("title", [None])[0] if isinstance(fields.get("title"), list) else fields.get("title"),
                    "category": fields.get("category", [None])[0] if isinstance(fields.get("category"), list) else fields.get("category")
                }
            })
        return output

    def delete(self, ids: List[str]) -> None:
        for id_ in ids:
            try:
                self.client.delete(index=self.collection_name, id=id_)
            except Exception:
                pass

    def teardown(self) -> Dict[str, Any]:
        try:
            self.client.indices.delete(index=self.collection_name)
            self.log_op(f"Deleted index '{self.collection_name}'")
        except Exception:
            pass

        if self.use_docker:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            self.log_op(f"Stopped and removed Docker container '{self.container_name}'")

        return {"memory_mb": None, "disk_mb": None}
