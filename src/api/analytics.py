"""
Analytics API endpoints.

This module provides REST API endpoints for retrieving chatbot usage analytics,
including query counts, latency metrics, feedback rates, and topic distributions.
"""

from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache
import hashlib

from fastapi import APIRouter, HTTPException, Query as QueryParam, status
from pydantic import BaseModel, Field, field_validator

from ..models.analytics import AnalyticsSummary
from ..services.analytics import analytics_service
from ..config.logging import logger


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


# Request/Response models
class AnalyticsSummaryRequest(BaseModel):
    """Request parameters for analytics summary."""
    start_date: datetime = Field(..., description="Start date (ISO 8601)")
    end_date: datetime = Field(..., description="End date (ISO 8601)")
    book_id: Optional[str] = Field(None, description="Filter by book ID")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Validate end_date > start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_not_future(cls, v: datetime) -> datetime:
        """Validate date is not in the future."""
        if v > datetime.utcnow():
            raise ValueError("Date cannot be in the future")
        return v


# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
_summary_cache = {}


def _get_cache_key(start_date: datetime, end_date: datetime, book_id: Optional[str]) -> str:
    """Generate cache key for analytics summary."""
    key_parts = [
        start_date.isoformat(),
        end_date.isoformat(),
        book_id or "all"
    ]
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def _is_cache_valid(cache_entry: dict) -> bool:
    """Check if cache entry is still valid."""
    if not cache_entry:
        return False

    cached_at = cache_entry.get('cached_at')
    if not cached_at:
        return False

    age = (datetime.utcnow() - cached_at).total_seconds()
    return age < CACHE_TTL_SECONDS


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Get Analytics Summary",
    description="""
    Retrieve comprehensive analytics summary for a specified time period.

    **Metrics included**:
    - Total queries and unique users
    - Latency percentiles (p50, p95, p99)
    - Feedback rates (overall and positive)
    - Average confidence score
    - Teacher time saved estimate
    - Top 10 question topics

    **Caching**: Results are cached for 5 minutes to reduce database load.

    **Example**:
    ```
    GET /v1/analytics/summary?start_date=2025-12-01T00:00:00Z&end_date=2025-12-11T23:59:59Z&book_id=physical-ai-robotics
    ```
    """
)
async def get_analytics_summary(
    start_date: datetime = QueryParam(..., description="Start date (ISO 8601 format)"),
    end_date: datetime = QueryParam(..., description="End date (ISO 8601 format)"),
    book_id: Optional[str] = QueryParam(None, description="Filter by book ID (optional)")
) -> AnalyticsSummary:
    """
    Get analytics summary for a time period.

    Args:
        start_date: Period start (ISO 8601)
        end_date: Period end (ISO 8601)
        book_id: Optional book filter

    Returns:
        AnalyticsSummary with all metrics

    Raises:
        HTTPException: 400 if validation fails, 500 if computation fails
    """
    try:
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be after start_date"
            )

        # Validate dates not in future
        now = datetime.utcnow()
        if start_date > now or end_date > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dates cannot be in the future"
            )

        # Check cache
        cache_key = _get_cache_key(start_date, end_date, book_id)
        cache_entry = _summary_cache.get(cache_key)

        if _is_cache_valid(cache_entry):
            logger.info(
                f"Analytics cache hit: {cache_key}",
                extra={
                    "cache_key": cache_key,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "book_id": book_id
                }
            )
            return cache_entry['data']

        # Compute analytics
        logger.info(
            f"Computing analytics summary",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "book_id": book_id
            }
        )

        summary = await analytics_service.get_analytics_summary(
            start_date=start_date,
            end_date=end_date,
            book_id=book_id
        )

        # Update cache
        _summary_cache[cache_key] = {
            'data': summary,
            'cached_at': datetime.utcnow()
        }

        # Clean up old cache entries (simple LRU: keep last 1000)
        if len(_summary_cache) > 1000:
            # Remove oldest entries
            sorted_keys = sorted(
                _summary_cache.keys(),
                key=lambda k: _summary_cache[k]['cached_at']
            )
            for old_key in sorted_keys[:100]:  # Remove oldest 100
                del _summary_cache[old_key]

        logger.info(
            f"Analytics computed successfully",
            extra={
                "total_queries": summary.total_queries,
                "unique_users": summary.unique_users,
                "cache_key": cache_key
            }
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Analytics computation failed: {str(e)}",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "book_id": book_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute analytics: {str(e)}"
        )


@router.get(
    "/low-confidence",
    summary="Get Low Confidence Queries",
    description="""
    Retrieve queries with low confidence scores or negative feedback.

    Used by teachers to identify content gaps and areas needing improvement.

    **Filters**:
    - confidence_threshold: Maximum confidence score (0-1)
    - include_negative_feedback: Include queries with negative feedback
    - book_id: Filter by book
    - chapter_number: Filter by chapter
    """
)
async def get_low_confidence_queries(
    start_date: datetime = QueryParam(..., description="Start date"),
    end_date: datetime = QueryParam(..., description="End date"),
    confidence_threshold: float = QueryParam(0.6, description="Max confidence score", ge=0.0, le=1.0),
    include_negative_feedback: bool = QueryParam(True, description="Include negative feedback"),
    book_id: Optional[str] = QueryParam(None, description="Filter by book"),
    chapter_number: Optional[int] = QueryParam(None, description="Filter by chapter"),
    limit: int = QueryParam(50, description="Max results", ge=1, le=500),
    offset: int = QueryParam(0, description="Skip N results", ge=0)
):
    """
    Get low confidence queries for content improvement.

    This endpoint will be implemented in Phase 5 (User Story 3).
    Currently returns placeholder response.
    """
    return {
        "message": "Low confidence query endpoint - to be implemented in User Story 3",
        "filters": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "confidence_threshold": confidence_threshold,
            "book_id": book_id,
            "chapter_number": chapter_number
        },
        "pagination": {
            "limit": limit,
            "offset": offset
        }
    }


@router.post(
    "/compute-aggregates",
    summary="Compute Daily Aggregates",
    description="""
    Manually trigger computation of daily aggregates.

    This can be called by a cron job or background scheduler to pre-compute
    daily metrics and store them in the analytics_aggregates table.

    **Note**: In production, this should be authenticated and restricted to admin users.
    """
)
async def compute_daily_aggregates(
    date: datetime = QueryParam(..., description="Date to compute aggregates for"),
    book_id: Optional[str] = QueryParam(None, description="Book filter")
):
    """
    Compute and store daily aggregates.

    Args:
        date: Date to compute aggregates for
        book_id: Optional book filter

    Returns:
        Summary of computed aggregates
    """
    try:
        logger.info(
            f"Computing daily aggregates",
            extra={
                "date": date.isoformat(),
                "book_id": book_id
            }
        )

        aggregates = await analytics_service.compute_daily_aggregates(
            date=date,
            book_id=book_id
        )

        logger.info(
            f"Aggregates computed: {len(aggregates)} records",
            extra={
                "date": date.isoformat(),
                "book_id": book_id,
                "count": len(aggregates)
            }
        )

        return {
            "status": "success",
            "date": date.isoformat(),
            "book_id": book_id,
            "aggregates_computed": len(aggregates),
            "metrics": [agg.metric_name for agg in aggregates]
        }

    except Exception as e:
        logger.error(
            f"Aggregate computation failed: {str(e)}",
            extra={
                "date": date.isoformat(),
                "book_id": book_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute aggregates: {str(e)}"
        )
