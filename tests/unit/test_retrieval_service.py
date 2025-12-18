"""Unit tests for RetrievalService.

Tests verify similarity threshold logic and refusal triggering.
Following TDD: These tests should FAIL until implementation is complete.
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4


class TestRetrievalService:
    """Unit tests for RetrievalService."""

    @pytest.mark.asyncio
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_retrieve_relevant_chunks_filters_by_threshold(self, mock_qdrant):
        """Test that chunks below similarity threshold are filtered out."""
        # Mock Qdrant search results with mixed scores
        mock_results = [
            {"id": str(uuid4()), "score": 0.85, "payload": {"text": "Relevant chunk 1"}},
            {"id": str(uuid4()), "score": 0.75, "payload": {"text": "Relevant chunk 2"}},
            {"id": str(uuid4()), "score": 0.65, "payload": {"text": "Irrelevant chunk"}},  # Below threshold
            {"id": str(uuid4()), "score": 0.72, "payload": {"text": "Relevant chunk 3"}},
        ]
        mock_qdrant.search.return_value = mock_results

        from backend.src.services.retrieval import RetrievalService

        retrieval_service = RetrievalService()

        # Retrieve with threshold 0.7
        query_embedding = [0.1] * 1536
        chunks = await retrieval_service.retrieve_relevant_chunks(
            query_embedding=query_embedding,
            top_k=5,
            threshold=0.7
        )

        # Should only return chunks >= 0.7
        assert len(chunks) == 3
        assert all(chunk["score"] >= 0.7 for chunk in chunks)
        assert all(chunk["score"] < 1.0 for chunk in chunks)  # Sanity check

    @pytest.mark.asyncio
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_retrieve_respects_top_k_limit(self, mock_qdrant):
        """Test that retrieval respects top_k parameter."""
        # Mock 10 results
        mock_results = [
            {"id": str(uuid4()), "score": 0.9 - (i * 0.05), "payload": {"text": f"Chunk {i}"}}
            for i in range(10)
        ]
        mock_qdrant.search.return_value = mock_results

        from backend.src.services.retrieval import RetrievalService

        retrieval_service = RetrievalService()

        query_embedding = [0.1] * 1536

        # Request only top 5
        chunks = await retrieval_service.retrieve_relevant_chunks(
            query_embedding=query_embedding,
            top_k=5,
            threshold=0.7
        )

        assert len(chunks) <= 5

    @pytest.mark.asyncio
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_no_results_above_threshold_returns_empty(self, mock_qdrant):
        """Test that no results above threshold returns empty list."""
        # Mock results all below threshold
        mock_results = [
            {"id": str(uuid4()), "score": 0.65, "payload": {"text": "Low score 1"}},
            {"id": str(uuid4()), "score": 0.60, "payload": {"text": "Low score 2"}},
        ]
        mock_qdrant.search.return_value = mock_results

        from backend.src.services.retrieval import RetrievalService

        retrieval_service = RetrievalService()

        query_embedding = [0.1] * 1536
        chunks = await retrieval_service.retrieve_relevant_chunks(
            query_embedding=query_embedding,
            top_k=5,
            threshold=0.7
        )

        assert len(chunks) == 0  # No chunks meet threshold

    @pytest.mark.asyncio
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_retrieve_includes_chunk_metadata(self, mock_qdrant):
        """Test that retrieved chunks include all required metadata."""
        mock_results = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "ZMP explanation...",
                    "chapter": "Module 0",
                    "section": "Locomotion",
                    "section_slug": "locomotion",
                    "source_file": "docs/chapters/module-0/locomotion.md"
                }
            }
        ]
        mock_qdrant.search.return_value = mock_results

        from backend.src.services.retrieval import RetrievalService

        retrieval_service = RetrievalService()

        query_embedding = [0.1] * 1536
        chunks = await retrieval_service.retrieve_relevant_chunks(
            query_embedding=query_embedding,
            top_k=5,
            threshold=0.7
        )

        assert len(chunks) == 1
        chunk = chunks[0]

        # Verify all required metadata fields
        assert "text" in chunk["payload"]
        assert "chapter" in chunk["payload"]
        assert "section" in chunk["payload"]
        assert "section_slug" in chunk["payload"]
        assert "source_file" in chunk["payload"]


class TestRefusalDetector:
    """Unit tests for RefusalDetector service."""

    def test_should_force_refusal_when_max_score_below_threshold(self):
        """Test that refusal is forced when max similarity is below threshold."""
        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        # All scores below 0.7
        similarity_scores = [0.65, 0.60, 0.55]

        should_refuse = refusal_detector.should_force_refusal(
            similarity_scores=similarity_scores,
            threshold=0.7
        )

        assert should_refuse is True

    def test_should_not_force_refusal_when_max_score_above_threshold(self):
        """Test that refusal is not forced when at least one score above threshold."""
        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        # At least one score above 0.7
        similarity_scores = [0.85, 0.65, 0.60]

        should_refuse = refusal_detector.should_force_refusal(
            similarity_scores=similarity_scores,
            threshold=0.7
        )

        assert should_refuse is False

    def test_should_force_refusal_with_empty_scores(self):
        """Test that empty similarity scores force refusal."""
        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        should_refuse = refusal_detector.should_force_refusal(
            similarity_scores=[],
            threshold=0.7
        )

        assert should_refuse is True

    def test_is_refusal_response_detects_keywords(self):
        """Test that refusal keywords are detected in response text."""
        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        refusal_responses = [
            "I don't have information about that topic in the book.",
            "The book does not contain information about weather forecasts.",
            "I cannot answer questions outside the scope of this book.",
        ]

        for response in refusal_responses:
            assert refusal_detector.is_refusal_response(response) is True

    def test_is_refusal_response_accepts_valid_responses(self):
        """Test that valid responses are not flagged as refusals."""
        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        valid_responses = [
            "Zero Moment Point (ZMP) is used for dynamic balance control.",
            "The book explains that humanoid robots use ZMP for walking.",
        ]

        for response in valid_responses:
            assert refusal_detector.is_refusal_response(response) is False
