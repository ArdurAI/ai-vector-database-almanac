#!/usr/bin/env python3
"""
pgvector VectorDBAdapter for the Almanac benchmark harness.

Dependencies: psycopg2-binary, pgvector (PostgreSQL extension)
"""

import time
import uuid
from typing import List, Dict, Any, Optional

from base_adapter import VectorDBAdapter


class PgvectorAdapter(VectorDBAdapter):
    """Adapter for pgvector (PostgreSQL extension)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.conn_string = config.get(
            "connection_string",
            "postgresql://postgres:postgres@localhost:5432/almanac"
        )
        self.conn = None
        self.cursor = None

    def setup(self, dimension: int, distance_metric: str) -> None:
        import psycopg2

        self.dimension = dimension
        self.distance_metric = distance_metric

        self.conn = psycopg2.connect(self.conn_string)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

        # Enable pgvector extension
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Drop table if exists
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.collection_name};")

        # Create table with vector column
        self.cursor.execute(f"""
            CREATE TABLE {self.collection_name} (
                id VARCHAR(64) PRIMARY KEY,
                embedding vector({dimension}),
                title TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        self.log_op(f"Created table '{self.collection_name}' with vector({dimension})")

    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        for vec, id_, meta in zip(vectors, ids, metadata):
            vec_str = "[" + ",".join(str(v) for v in vec) + "]"
            self.cursor.execute(f"""
                INSERT INTO {self.collection_name} (id, embedding, title, category)
                VALUES (%s, %s::vector, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    title = EXCLUDED.title,
                    category = EXCLUDED.category;
            """, (id_, vec_str, meta.get("title", ""), meta.get("category", "")))
        self.log_op(f"Upserted {len(vectors)} vectors")

    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        metric_map = {
            "cosine": "vector_cosine_ops",
            "euclidean": "vector_l2_ops",
            "dot_product": "vector_ip_ops"
        }
        ops = metric_map.get(self.distance_metric, "vector_cosine_ops")

        if index_type == "hnsw":
            m = params.get("m", 16) if params else 16
            ef_construction = params.get("ef_construction", 64) if params else 64
            self.cursor.execute(f"""
                CREATE INDEX ON {self.collection_name}
                USING hnsw (embedding {ops})
                WITH (m = {m}, ef_construction = {ef_construction});
            """)
            self.log_op(f"Built HNSW index: m={m}, ef_construction={ef_construction}, ops={ops}")
        elif index_type == "ivfflat":
            lists = params.get("lists", 100) if params else 100
            self.cursor.execute(f"""
                CREATE INDEX ON {self.collection_name}
                USING ivfflat (embedding {ops})
                WITH (lists = {lists});
            """)
            self.log_op(f"Built IVFFlat index: lists={lists}, ops={ops}")
        else:
            self.log_op(f"No index built (type={index_type})")

    def await_ready(self) -> None:
        # PostgreSQL indexes are synchronous on creation
        # But we run ANALYZE to update statistics
        start = time.time()
        self.cursor.execute(f"ANALYZE {self.collection_name};")
        elapsed = time.time() - start
        self.log_op(f"await_ready completed in {elapsed:.2f}s (ANALYZE done)")

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        where_clauses = []
        params = [vec_str, top_k]
        if filters:
            for k, v in filters.items():
                where_clauses.append(f"{k} = %s")
                params.append(v)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Distance operator depends on metric
        metric_map = {
            "cosine": "embedding <=> %s",
            "euclidean": "embedding <-> %s",
            "dot_product": "embedding <#> %s"
        }
        distance_expr = metric_map.get(self.distance_metric, "embedding <=> %s")

        # For cosine, lower distance = more similar. For dot_product, higher = more similar.
        order = "ASC" if self.distance_metric in ("cosine", "euclidean") else "DESC"

        self.cursor.execute(f"""
            SELECT id, {distance_expr} AS distance, title, category
            FROM {self.collection_name}
            {where_sql}
            ORDER BY distance {order}
            LIMIT %s;
        """, params)

        rows = self.cursor.fetchall()
        return [
            {"id": row[0], "distance": row[1], "metadata": {"title": row[2], "category": row[3]}}
            for row in rows
        ]

    def delete(self, ids: List[str]) -> None:
        placeholders = ",".join(["%s"] * len(ids))
        self.cursor.execute(f"DELETE FROM {self.collection_name} WHERE id IN ({placeholders});", ids)

    def teardown(self) -> Dict[str, Any]:
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.collection_name};")
        self.log_op(f"Dropped table '{self.collection_name}'")
        self.cursor.close()
        self.conn.close()

        return {"memory_mb": None, "disk_mb": None}
