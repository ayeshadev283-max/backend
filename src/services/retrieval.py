"""Retrieval service for semantic search in Qdrant."""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from ..db.qdrant import qdrant_client
from ..models.config import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for semantic search and chunk retrieval."""

    def __init__(
        self,
        top_k: int = None,
        similarity_threshold: float = None
    ):
        """
        Initialize retrieval service.

        Args:
            top_k: Number of chunks to retrieve (default from settings)
            similarity_threshold: Minimum similarity score (default from settings)
        """
        self.top_k = top_k or settings.top_k_retrieval
        self.similarity_threshold = similarity_threshold or settings.similarity_threshold

    def retrieve_chunks(
        self,
        query_embedding: List[float],
        book_id: Optional[str] = None,
        chapter_number: Optional[int] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks based on query embedding.

        Args:
            query_embedding: Query vector (1536 dimensions)
            book_id: Filter by book ID
            chapter_number: Filter by chapter number
            top_k: Override default top_k
            similarity_threshold: Override default threshold

        Returns:
            List of retrieved chunks with scores and metadata
        """
        # Use provided values or defaults
        k = top_k or self.top_k
        threshold = similarity_threshold or self.similarity_threshold

        # Build filter conditions
        filter_conditions = None
        if book_id or chapter_number:
            filter_conditions = {"must": []}

            if book_id:
                filter_conditions["must"].append({
                    "key": "book_id",
                    "match": {"value": book_id}
                })

            if chapter_number:
                filter_conditions["must"].append({
                    "key": "chapter_number",
                    "match": {"value": chapter_number}
                })

        # Perform search
        try:
            results = qdrant_client.search(
                query_vector=query_embedding,
                top_k=k,
                score_threshold=threshold,
                filter_conditions=filter_conditions
            )

            logger.info(
                f"Retrieved {len(results)} chunks "
                f"(threshold: {threshold}, book_id: {book_id}, chapter: {chapter_number})"
            )

            return results

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise

    def extract_source_references(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract source references from retrieved chunks.

        Args:
            chunks: List of chunks with payload containing metadata

        Returns:
            List of source reference dicts
        """
        references = []

        for chunk in chunks:
            payload = chunk.get('payload', {})
            chunk_id = chunk.get('id')

            reference = {
                "chapter": str(payload.get('chapter_number', '?')),
                "section": payload.get('section'),
                "citation": self._format_citation(payload),
                "chunk_id": chunk_id
            }

            references.append(reference)

        return references

    def _format_citation(self, payload: Dict[str, Any]) -> str:
        """
        Format a citation string from chunk metadata.

        Args:
            payload: Chunk payload with metadata

        Returns:
            Formatted citation string
        """
        chapter = payload.get('chapter_number', '?')
        section = payload.get('section', '')

        if section:
            return f"Chapter {chapter}, {section}"
        else:
            return f"Chapter {chapter}"

    def calculate_confidence_score(
        self,
        similarity_scores: List[float]
    ) -> float:
        """
        Calculate confidence score from similarity scores.

        Args:
            similarity_scores: List of similarity scores from retrieval

        Returns:
            Confidence score (0.0-1.0)
        """
        if not similarity_scores:
            return 0.0

        # Use average of top scores as confidence
        avg_score = sum(similarity_scores) / len(similarity_scores)

        return round(avg_score, 2)


# Global retrieval service instance
retrieval_service = RetrievalService()
