"""Query API endpoint for RAG chatbot."""
import logging
import hashlib
import time
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..models.query import (
    QueryRequest,
    QueryResponse,
    SourceReference
)
from ..services.embedding import embedding_service
from ..services.retrieval import retrieval_service
from ..services.generation import generation_service
from ..db.postgres import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter()


# Simple in-memory rate limiter (production would use Redis)
rate_limit_store = {}


def check_rate_limit(user_id: str, limit_per_hour: int = 60) -> bool:
    """
    Check if user has exceeded rate limit.

    Args:
        user_id: User identifier
        limit_per_hour: Maximum queries per hour

    Returns:
        True if within limit, False if exceeded
    """
    from ..models.config import settings

    current_time = time.time()
    hour_ago = current_time - 3600

    # Clean old entries
    if user_id in rate_limit_store:
        rate_limit_store[user_id] = [
            t for t in rate_limit_store[user_id] if t > hour_ago
        ]

    # Check limit
    user_requests = rate_limit_store.get(user_id, [])

    if len(user_requests) >= settings.rate_limit_per_hour:
        return False

    # Add new request
    if user_id not in rate_limit_store:
        rate_limit_store[user_id] = []

    rate_limit_store[user_id].append(current_time)
    return True


def anonymize_user_id(request: Request) -> str:
    """
    Create anonymized user ID from IP and user agent.

    Args:
        request: FastAPI request object

    Returns:
        SHA-256 hash of user identifiers
    """
    # Use IP address and user agent to create unique but anonymous ID
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    combined = f"{ip}:{user_agent}"
    hash_obj = hashlib.sha256(combined.encode())

    return hash_obj.hexdigest()


@router.post("/query", response_model=QueryResponse, tags=["query"])
async def submit_query(
    query_request: QueryRequest,
    request: Request
) -> QueryResponse:
    """
    Submit a query and receive AI-generated answer.

    Processes a user's natural language question about book content and returns
    an accurate, source-grounded answer with citations.

    **Workflow:**
    1. Convert query to embedding vector
    2. Retrieve top-N relevant book chunks from vector database
    3. Generate response using AI model with retrieved context
    4. Return answer with source references

    **Latency:** Typically 1-3 seconds (p95 < 3s)
    """
    start_time = time.time()
    query_id = uuid4()

    # Anonymize user ID
    user_id = anonymize_user_id(request)

    # Check rate limit (T035)
    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Maximum 60 queries per hour exceeded. Please try again later.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )

    try:
        # Step 1: Embed query (T027)
        logger.info(f"Processing query {query_id}: {query_request.query[:50]}...")

        try:
            query_embedding = embedding_service.embed_text(query_request.query)
        except Exception as e:
            # Error handling for embedding failures (T033)
            logger.error(f"Embedding failed for query {query_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service temporarily unavailable",
                    "message": "Failed to process query. Please try again.",
                    "code": "EMBEDDING_FAILED"
                }
            )

        # Step 2: Retrieve relevant chunks (T027)
        try:
            retrieved_chunks = retrieval_service.retrieve_chunks(
                query_embedding=query_embedding,
                book_id=query_request.book_context.book_id,
                chapter_number=query_request.book_context.chapter_number
            )
        except Exception as e:
            # Error handling for Qdrant failures (T034)
            logger.error(f"Retrieval failed for query {query_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service temporarily unavailable",
                    "message": "Failed to retrieve relevant content. Please try again.",
                    "code": "RETRIEVAL_FAILED"
                }
            )

        # Extract similarity scores for confidence calculation
        similarity_scores = [chunk['score'] for chunk in retrieved_chunks]

        # Handle insufficient context (T032)
        if not retrieved_chunks:
            logger.warning(f"No chunks retrieved for query {query_id}")

        # Step 3: Generate response (T027)
        try:
            generation_result = generation_service.generate_response(
                user_query=query_request.query,
                retrieved_chunks=retrieved_chunks,
                book_title=query_request.book_context.book_id.replace('-', ' ').title()
            )
        except Exception as e:
            # Error handling for OpenAI failures (T033)
            logger.error(f"Generation failed for query {query_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Service temporarily unavailable",
                    "message": "Failed to generate response. Please try again.",
                    "code": "GENERATION_FAILED"
                }
            )

        # Extract source references
        source_references_data = retrieval_service.extract_source_references(retrieved_chunks)
        source_references = [SourceReference(**ref) for ref in source_references_data]

        # Calculate confidence score
        confidence_score = retrieval_service.calculate_confidence_score(similarity_scores)

        # Calculate total latency
        total_latency_ms = int((time.time() - start_time) * 1000)

        # Step 4: Log query to database (T029)
        try:
            await _log_query(
                query_id=query_id,
                user_id=user_id,
                query_text=query_request.query,
                query_embedding=query_embedding,
                selected_text=query_request.selected_text,
                book_context=query_request.book_context.model_dump(),
                ip_address_hash=hashlib.sha256(
                    request.client.host.encode() if request.client else b"unknown"
                ).hexdigest()
            )
        except Exception as e:
            logger.error(f"Failed to log query {query_id}: {e}")
            # Don't fail the request if logging fails

        # Step 5: Log retrieved context (T030)
        try:
            await _log_retrieved_context(
                query_id=query_id,
                chunk_ids=[UUID(chunk['id']) for chunk in retrieved_chunks],
                similarity_scores=similarity_scores,
                retrieval_params={
                    "top_k": len(retrieved_chunks),
                    "similarity_threshold": retrieval_service.similarity_threshold,
                    "filter": {
                        "book_id": query_request.book_context.book_id,
                        "chapter_number": query_request.book_context.chapter_number
                    },
                    "retrieval_strategy": "vector_search"
                }
            )
        except Exception as e:
            logger.error(f"Failed to log retrieved context for {query_id}: {e}")

        # Step 6: Log response (T031)
        try:
            await _log_response(
                query_id=query_id,
                response_text=generation_result['response_text'],
                source_references=[ref.model_dump() for ref in source_references],
                generation_params=generation_result['generation_params'],
                latency_ms=total_latency_ms,
                confidence_score=confidence_score
            )
        except Exception as e:
            logger.error(f"Failed to log response for {query_id}: {e}")

        # Return response
        response = QueryResponse(
            query_id=query_id,
            response_text=generation_result['response_text'],
            source_references=source_references,
            confidence_score=confidence_score,
            latency_ms=total_latency_ms
        )

        logger.info(
            f"Query {query_id} completed successfully "
            f"(latency: {total_latency_ms}ms, confidence: {confidence_score})"
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Catch-all error handler
        logger.error(f"Unexpected error processing query {query_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while processing your query.",
                "code": "INTERNAL_ERROR"
            }
        )


async def _log_query(
    query_id: UUID,
    user_id: str,
    query_text: str,
    query_embedding: list,
    selected_text: Optional[str],
    book_context: dict,
    ip_address_hash: str
):
    """Log query to database (T029)."""
    import json

    query_sql = """
        INSERT INTO queries (
            query_id, user_id, query_text, query_embedding,
            selected_text, book_context, timestamp, ip_address_hash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    await postgres_client.execute(
        query_sql,
        (
            str(query_id),
            user_id,
            query_text,
            str(query_embedding),  # Store as string (would use pgvector in production)
            selected_text,
            json.dumps(book_context),
            datetime.utcnow(),
            ip_address_hash
        )
    )


async def _log_retrieved_context(
    query_id: UUID,
    chunk_ids: list,
    similarity_scores: list,
    retrieval_params: dict
):
    """Log retrieved context to database (T030)."""
    import json

    context_sql = """
        INSERT INTO retrieved_contexts (
            query_id, chunk_ids, similarity_scores, retrieval_params, timestamp
        ) VALUES (%s, %s, %s, %s, %s)
    """

    await postgres_client.execute(
        context_sql,
        (
            str(query_id),
            [str(cid) for cid in chunk_ids],
            similarity_scores,
            json.dumps(retrieval_params),
            datetime.utcnow()
        )
    )


async def _log_response(
    query_id: UUID,
    response_text: str,
    source_references: list,
    generation_params: dict,
    latency_ms: int,
    confidence_score: float
):
    """Log response to database (T031)."""
    import json

    response_sql = """
        INSERT INTO query_responses (
            query_id, response_text, source_references,
            generation_params, latency_ms, timestamp, confidence_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    await postgres_client.execute(
        response_sql,
        (
            str(query_id),
            response_text,
            json.dumps(source_references),
            json.dumps(generation_params),
            latency_ms,
            datetime.utcnow(),
            confidence_score
        )
    )
