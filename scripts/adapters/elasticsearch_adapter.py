#!/usr/bin/env python3
"""
Elasticsearch VectorDBAdapter for the Almanac benchmark harness.

Dependencies: elasticsearch>=9.0.0

Docker:
    docker run -d --name es-almanac -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.15.0
"""

import time
import subprocess
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class ElasticsearchAdapter(VectorDBAdapter):
    """Adapter for Elasticsearch 8.x with dense_vector KNN."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 9200)
        self.use_docker = config.get("use_docker", True)
        self.container_name = config.get("container_name", "es-almanac")
        self.client = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        from elasticsearch import Elasticsearch

        self.dimension = dimension
        self.distance_metric = distance_metric

        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2_norm",
            "dot_product": "dot_product"
        }
        es_metric = metric_map.get(distance_metric, "cosine")

        if self.use_docker:
            subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
            time.sleep(1)
            subprocess.run([
                "docker", "run", "-d", "--name", self.container_name,
                "-p", "9200:9200",
                "-e", "discovery.type=single-node",
                "-e", "xpack.security.enabled=false",
                "-e", "ES_JAVA_OPTS=-Xms512m -Xmx512m",
                "docker.elastic.co/elasticsearch/elasticsearch:8.15.0"
            ], check=True, capture_output=True)
            # Poll until Elasticsearch is ready
            for _ in range(120):
                try:
                    es = Elasticsearch([f"http://{self.host}:{self.port}"])
                    if es.ping():
                        break
                except Exception:
                    time.sleep(1)
            else:
                raise TimeoutError("Elasticsearch did not become ready within 120 seconds")

        self.client = Elasticsearch([f"http://{self.host}:{self.port}"])
        self.client.ping()

        # Delete index if exists
        try:
            self.client.indices.delete(index=self.collection_name)
        except Exception:
            pass

        # Create index with dense_vector mapping
        self.client.indices.create(
            index=self.collection_name,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "dense_vector",
                            "dims": dimension,
                            "index": True,
                            "similarity": es_metric
                        },
                        "title": {"type": "text"},
                        "category": {"type": "keyword"}
                    }
                }
            }
        )
        self.log_op(f"Created ES index '{self.collection_name}' with dim={dimension}, metric={es_metric}")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        from elasticsearch.helpers import bulk

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
        # Elasticsearch dense_vector index is built during indexing with index: true
        # Refresh to make all docs searchable and trigger index merge
        self.client.indices.refresh(index=self.collection_name)
        self.log_op("Refreshed index (dense_vector auto-indexed during ingestion)")

    def await_ready(self) -> None:
        start = time.time()
        self.client.indices.refresh(index=self.collection_name)
        # Wait for index status green
        self.client.cluster.health(wait_for_status="green", timeout="30s")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (index green)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        knn_body = {
            "field": "vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 10
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
                "knn": knn_body,
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
