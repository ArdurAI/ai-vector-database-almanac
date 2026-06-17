#!/usr/bin/env python3
"""
Base VectorDBAdapter contract.
All tool-specific adapters inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorDBAdapter(ABC):
    """
    Frozen adapter contract for the Vector Databases & RAG Infrastructure Almanac.
    Each tool must implement this interface to be benchmarked.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dimension = None
        self.distance_metric = None
        self.collection_name = config.get("collection_name", "almanac-test")
        self.ops_notes = []

    @abstractmethod
    def setup(self, dimension: int, distance_metric: str) -> None:
        """
        Install, configure, and start the tool. Create a collection.
        
        Args:
            dimension: Vector dimension (e.g., 384, 768, 1536)
            distance_metric: "cosine", "euclidean", or "dot_product"
        """
        pass

    @abstractmethod
    def load(self, vectors: List[List[float]], ids: List[str], metadata: List[Dict]) -> None:
        """
        Ingest the vectors into the collection.
        
        Args:
            vectors: List of vector embeddings
            ids: List of string IDs (same length as vectors)
            metadata: List of metadata dicts (same length as vectors)
        """
        pass

    @abstractmethod
    def build_index(self, index_type: str, params: Optional[Dict] = None) -> None:
        """
        Build the ANN index with specified parameters.
        
        Args:
            index_type: "hnsw", "ivf", "flat", etc.
            params: Tool-specific index parameters. Must be logged.
        """
        pass

    @abstractmethod
    def await_ready(self) -> None:
        """
        Wait for async indexing to complete. Measure lag.
        This is where async-ingestion designs get their cost measured.
        """
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Run the query and return the top-k results with IDs and distances.
        
        Args:
            query_vector: The query embedding
            top_k: Number of results to return
            filters: Optional metadata filters (dict)
        
        Returns:
            List of dicts with keys: "id" (str), "distance" (float), "metadata" (dict)
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by ID.
        """
        pass

    @abstractmethod
    def teardown(self) -> Dict[str, Any]:
        """
        Clean up, drop collection, measure resource usage.
        
        Returns:
            Dict with resource usage metrics (memory, disk, etc.)
        """
        pass

    def log_op(self, note: str) -> None:
        """Log an operational note for the benchmark record."""
        self.ops_notes.append(note)

    def get_ops_notes(self) -> List[str]:
        """Return all operational notes."""
        return self.ops_notes
