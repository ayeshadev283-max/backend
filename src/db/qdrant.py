"""Qdrant vector database client wrapper."""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from ..models.config import settings

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Wrapper for Qdrant client with connection pooling and error handling."""

    def __init__(self):
        """Initialize Qdrant client connection."""
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.qdrant_collection_name

    def connect(self):
        """Establish connection to Qdrant."""
        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
                timeout=30.0
            )
            logger.info(f"Connected to Qdrant at {settings.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def ensure_collection(self, vector_size: int = 1536):
        """Create collection if it doesn't exist."""
        if not self.client:
            self.connect()

        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )

                # Create payload indexes for filtering
                from qdrant_client.models import PayloadSchemaType
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="book_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )

                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")

                # Ensure indexes exist
                try:
                    from qdrant_client.models import PayloadSchemaType
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="book_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                except Exception:
                    pass  # Index might already exist
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Upsert chunks to Qdrant collection.

        Args:
            chunks: List of dicts with 'id', 'vector', 'payload' keys
        """
        if not self.client:
            self.connect()

        try:
            points = [
                PointStruct(
                    id=chunk["id"],
                    vector=chunk["vector"],
                    payload=chunk.get("payload", {})
                )
                for chunk in chunks
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(chunks)} chunks to {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filter_conditions: Optional metadata filter

        Returns:
            List of search results with id, score, and payload
        """
        if not self.client:
            self.connect()

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=filter_conditions
            )

            results = [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in search_result
            ]

            logger.info(f"Found {len(results)} results above threshold {score_threshold}")
            return results

        except UnexpectedResponse as e:
            logger.error(f"Qdrant search failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def close(self):
        """Close Qdrant client connection."""
        if self.client:
            self.client.close()
            logger.info("Closed Qdrant connection")


# Global Qdrant client instance
qdrant_client = QdrantClientWrapper()
