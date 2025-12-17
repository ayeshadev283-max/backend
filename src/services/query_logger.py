"""Query logger service for persisting queries and responses to PostgreSQL.

Logs all queries, retrieved contexts, and responses for analytics and debugging.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QueryLogger:
    """Log queries and responses to PostgreSQL for analytics."""

    def __init__(self, db_pool=None):
        """Initialize query logger with database connection pool."""
        self.db_pool = db_pool

    async def log_query(
        self,
        query_id: UUID,
        user_id: str,
        query_text: str,
        query_mode: str,
        book_context: Dict[str, Any],
        selected_text: Optional[str] = None,
        session_id: Optional[UUID] = None
    ) -> None:
        """
        Log user query to queries table.

        Args:
            query_id: Unique query identifier
            user_id: User identifier
            query_text: The query text
            query_mode: "book-wide" or "selected-text"
            book_context: Book metadata (book_id, title, version)
            selected_text: Selected text (for selected-text mode)
            session_id: Optional session identifier
        """
        if not self.db_pool:
            logger.warning("Database pool not configured, skipping query logging")
            return

        query = """
            INSERT INTO queries (
                query_id, user_id, query_text, query_mode,
                book_context, selected_text, session_id, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        try:
            async with self.db_pool.connection() as conn:
                await conn.execute(
                    query,
                    query_id,
                    user_id,
                    query_text,
                    query_mode,
                    book_context,  # JSONB
                    selected_text,
                    session_id,
                    datetime.utcnow()
                )
            logger.info(f"Logged query {query_id} (mode: {query_mode})")

        except Exception as e:
            logger.error(f"Failed to log query {query_id}: {e}", exc_info=True)
            # Don't raise - logging failure shouldn't break the request

    async def log_response(
        self,
        response_id: UUID,
        query_id: UUID,
        response_text: str,
        source_references: List[Dict[str, Any]],
        generation_params: Dict[str, Any],
        latency_ms: int,
        confidence_score: Optional[float] = None,
        refusal_triggered: bool = False,
        refusal_reason: Optional[str] = None
    ) -> None:
        """
        Log generated response to query_responses table.

        Args:
            response_id: Unique response identifier
            query_id: Associated query ID
            response_text: Generated response text
            source_references: List of citation objects
            generation_params: LLM parameters (model, temperature, max_tokens)
            latency_ms: Response latency in milliseconds
            confidence_score: Optional confidence score (0.0-1.0)
            refusal_triggered: Whether deterministic refusal was triggered
            refusal_reason: Reason for refusal if applicable
        """
        if not self.db_pool:
            logger.warning("Database pool not configured, skipping response logging")
            return

        query = """
            INSERT INTO query_responses (
                response_id, query_id, response_text, source_references,
                generation_params, latency_ms, confidence_score,
                refusal_triggered, refusal_reason, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """

        try:
            async with self.db_pool.connection() as conn:
                await conn.execute(
                    query,
                    response_id,
                    query_id,
                    response_text,
                    source_references,  # JSONB
                    generation_params,  # JSONB
                    latency_ms,
                    confidence_score,
                    refusal_triggered,
                    refusal_reason,
                    datetime.utcnow()
                )
            logger.info(f"Logged response {response_id} for query {query_id}")

        except Exception as e:
            logger.error(f"Failed to log response {response_id}: {e}", exc_info=True)

    async def log_retrieved_contexts(
        self,
        query_id: UUID,
        chunks: List[Dict[str, Any]]
    ) -> None:
        """
        Log retrieved chunks to retrieved_contexts table.

        Args:
            query_id: Associated query ID
            chunks: List of retrieved chunks with scores and metadata
        """
        if not self.db_pool:
            logger.warning("Database pool not configured, skipping context logging")
            return

        if not chunks:
            return

        query = """
            INSERT INTO retrieved_contexts (
                retrieval_id, query_id, chunk_id, qdrant_point_id,
                chunk_text, similarity_score, rank, metadata, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        try:
            async with self.db_pool.connection() as conn:
                for rank, chunk in enumerate(chunks, start=1):
                    from uuid import uuid4

                    retrieval_id = uuid4()
                    chunk_id = chunk.get("id")
                    qdrant_point_id = chunk.get("id")  # Same as chunk_id in our case
                    chunk_text = chunk.get("payload", {}).get("text", "")
                    similarity_score = chunk.get("score", 0.0)
                    metadata = chunk.get("payload", {})

                    await conn.execute(
                        query,
                        retrieval_id,
                        query_id,
                        chunk_id,
                        qdrant_point_id,
                        chunk_text,
                        similarity_score,
                        rank,
                        metadata,  # JSONB
                        datetime.utcnow()
                    )

            logger.info(f"Logged {len(chunks)} retrieved contexts for query {query_id}")

        except Exception as e:
            logger.error(f"Failed to log retrieved contexts for query {query_id}: {e}", exc_info=True)


# Global query logger instance (will be initialized with db_pool in main.py)
query_logger = QueryLogger()
