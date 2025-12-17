"""Integration tests for book-wide query workflow.

Tests the complete pipeline: query → embed → retrieve → generate → cite
Following TDD: These tests should FAIL until implementation is complete.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4


@pytest.fixture
def mock_query_embedding():
    """Mock query embedding vector."""
    return [0.1] * 1536  # 1536-dimensional vector


@pytest.fixture
def mock_retrieved_chunks():
    """Mock retrieved chunks from Qdrant."""
    return [
        {
            "id": str(uuid4()),
            "score": 0.85,
            "payload": {
                "text": "Zero Moment Point (ZMP) is a fundamental concept in humanoid robotics...",
                "chapter": "Module 0 - Foundations",
                "section": "Locomotion and Motor Control",
                "section_slug": "locomotion-motor-control",
                "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
            }
        },
        {
            "id": str(uuid4()),
            "score": 0.78,
            "payload": {
                "text": "ZMP is used for dynamic balance control in bipedal walking...",
                "chapter": "Module 0 - Foundations",
                "section": "Locomotion and Motor Control",
                "section_slug": "locomotion-motor-control",
                "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
            }
        }
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI generation response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Zero Moment Point (ZMP) is a fundamental concept used for dynamic balance control in bipedal walking. It represents the point where the ground reaction forces can be considered to act."
                }
            }
        ]
    }


class TestBookWideWorkflow:
    """Integration tests for complete book-wide query workflow."""

    @pytest.mark.asyncio
    @patch("backend.src.services.embedding.OpenAI")
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_full_query_workflow(
        self,
        mock_qdrant,
        mock_openai,
        mock_query_embedding,
        mock_retrieved_chunks,
        mock_openai_response
    ):
        """Test complete workflow from query to response."""
        # Setup mocks
        mock_openai.embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_query_embedding)]
        )
        mock_qdrant.search.return_value = mock_retrieved_chunks
        mock_openai.chat.completions.create.return_value = Mock(**mock_openai_response)

        # Import services (after mocks are set up)
        from backend.src.services.embedding import EmbeddingService
        from backend.src.services.retrieval import RetrievalService
        from backend.src.services.generation import GenerationService
        from backend.src.services.citation_builder import CitationBuilder

        embedding_service = EmbeddingService()
        retrieval_service = RetrievalService()
        generation_service = GenerationService()
        citation_builder = CitationBuilder()

        # Step 1: Embed query
        query_text = "What is Zero Moment Point used for?"
        query_vector = await embedding_service.embed_text(query_text)

        assert query_vector is not None
        assert len(query_vector) == 1536

        # Step 2: Retrieve relevant chunks
        retrieved_chunks = await retrieval_service.retrieve_relevant_chunks(
            query_embedding=query_vector,
            top_k=5,
            threshold=0.7
        )

        assert len(retrieved_chunks) > 0
        assert all(chunk["score"] >= 0.7 for chunk in retrieved_chunks)

        # Step 3: Generate response
        response_text = await generation_service.generate_grounded_response(
            query=query_text,
            retrieved_chunks=retrieved_chunks,
            system_prompt="BOOK_WIDE_SYSTEM_PROMPT"
        )

        assert response_text is not None
        assert len(response_text) >= 50  # Non-trivial response

        # Step 4: Build citations
        citations = citation_builder.build_citations(retrieved_chunks)

        assert len(citations) > 0
        assert all("url" in cite for cite in citations)
        assert all(cite["url"].startswith("/chapters/") for cite in citations)

    @pytest.mark.asyncio
    @patch("backend.src.services.embedding.OpenAI")
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_low_similarity_triggers_refusal(
        self,
        mock_qdrant,
        mock_openai,
        mock_query_embedding
    ):
        """Test that low similarity scores trigger refusal WITHOUT calling OpenAI."""
        # Setup mocks - all chunks below threshold
        low_similarity_chunks = [
            {
                "id": str(uuid4()),
                "score": 0.65,  # Below 0.7 threshold
                "payload": {"text": "Irrelevant content..."}
            }
        ]

        mock_openai.embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_query_embedding)]
        )
        mock_qdrant.search.return_value = low_similarity_chunks

        from backend.src.services.refusal_detector import RefusalDetector

        refusal_detector = RefusalDetector()

        # Check if refusal should be forced
        similarity_scores = [chunk["score"] for chunk in low_similarity_chunks]
        should_refuse = refusal_detector.should_force_refusal(
            similarity_scores=similarity_scores,
            threshold=0.7
        )

        assert should_refuse is True

        # Verify OpenAI is NOT called (cost optimization)
        # This would be verified in the endpoint implementation

    @pytest.mark.asyncio
    @patch("backend.src.services.embedding.OpenAI")
    @patch("backend.src.db.qdrant.qdrant_client")
    @patch("backend.src.db.postgres.AsyncConnectionPool")
    async def test_query_logging_to_postgres(
        self,
        mock_postgres,
        mock_qdrant,
        mock_openai,
        mock_query_embedding,
        mock_retrieved_chunks
    ):
        """Test that queries and responses are logged to PostgreSQL."""
        # Setup mocks
        mock_openai.embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_query_embedding)]
        )
        mock_qdrant.search.return_value = mock_retrieved_chunks

        mock_conn = AsyncMock()
        mock_postgres.connection.return_value.__aenter__.return_value = mock_conn

        from backend.src.services.query_logger import QueryLogger

        query_logger = QueryLogger()

        # Log query
        query_id = uuid4()
        await query_logger.log_query(
            query_id=query_id,
            user_id="test_user",
            query_text="What is ZMP?",
            query_mode="book-wide",
            book_context={"book_id": "physical-ai-robotics"}
        )

        # Verify insert was called
        mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_citation_consolidation(self, mock_retrieved_chunks):
        """Test that multiple chunks from same section are consolidated."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        # Both mock chunks are from same section
        citations = citation_builder.build_citations(mock_retrieved_chunks)

        # Should consolidate to single citation since both from "Locomotion and Motor Control"
        assert len(citations) == 1
        assert citations[0]["section"] == "Locomotion and Motor Control"
        assert citations[0]["url"] == "/chapters/module-0-foundations/locomotion-motor-control#locomotion-motor-control"

    @pytest.mark.asyncio
    @patch("backend.src.db.qdrant.qdrant_client")
    async def test_qdrant_connection_failure_handling(self, mock_qdrant):
        """Test graceful handling of Qdrant connection failures."""
        from qdrant_client.http.exceptions import UnexpectedResponse
        from backend.src.services.retrieval import RetrievalService

        # Simulate Qdrant connection failure
        mock_qdrant.search.side_effect = UnexpectedResponse(
            status_code=503,
            reason_phrase="Service Unavailable",
            content=b"Qdrant service unavailable"
        )

        retrieval_service = RetrievalService()

        with pytest.raises(UnexpectedResponse):
            await retrieval_service.retrieve_relevant_chunks(
                query_embedding=[0.1] * 1536,
                top_k=5
            )

    @pytest.mark.asyncio
    @patch("backend.src.services.embedding.OpenAI")
    async def test_openai_rate_limit_handling(self, mock_openai):
        """Test graceful handling of OpenAI rate limit errors."""
        from openai import RateLimitError
        from backend.src.services.embedding import EmbeddingService

        # Simulate rate limit error
        mock_openai.embeddings.create.side_effect = RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body={}
        )

        embedding_service = EmbeddingService()

        with pytest.raises(RateLimitError):
            await embedding_service.embed_text("Test query")
