"""
Pydantic models for analytics data structures.

This module defines data models for analytics aggregates, metrics summaries,
and related analytics data structures used by the RAG chatbot system.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class AnalyticsAggregate(BaseModel):
    """
    Analytics aggregate record.

    Stores pre-computed analytics metrics for dashboard performance.
    Aggregates can represent daily/weekly/monthly summaries of various metrics.
    """
    aggregate_id: UUID = Field(default_factory=uuid4, description="Unique aggregate identifier")
    metric_name: str = Field(..., description="Metric identifier (e.g., 'daily_query_count', 'weekly_avg_latency')")
    time_period_start: datetime = Field(..., description="Period start timestamp")
    time_period_end: datetime = Field(..., description="Period end timestamp")
    metric_value: Dict[str, Any] = Field(..., description="Aggregated metric data (JSONB)")
    book_id: Optional[str] = Field(None, description="Book identifier (null for global metrics)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Aggregate computation time")

    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v: str) -> str:
        """Validate metric name is from allowed set."""
        allowed_metrics = {
            'daily_query_count',
            'weekly_avg_latency',
            'monthly_feedback_rate',
            'top_question_topics',
            'hourly_concurrent_users'
        }
        if v not in allowed_metrics:
            raise ValueError(f"Invalid metric_name: {v}. Must be one of {allowed_metrics}")
        return v

    @field_validator('time_period_end')
    @classmethod
    def validate_time_period(cls, v: datetime, info) -> datetime:
        """Validate time_period_end > time_period_start."""
        if 'time_period_start' in info.data and v <= info.data['time_period_start']:
            raise ValueError("time_period_end must be after time_period_start")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "aggregate_id": "d4e5f6g7-h8i9-0j1k-2l3m-n4o5p6q7r8s9",
                "metric_name": "daily_query_count",
                "time_period_start": "2025-12-11T00:00:00Z",
                "time_period_end": "2025-12-11T23:59:59Z",
                "metric_value": {
                    "total_queries": 1247,
                    "unique_users": 387
                },
                "book_id": "physical-ai-robotics",
                "created_at": "2025-12-12T00:05:00Z"
            }
        }


class AnalyticsSummary(BaseModel):
    """
    Analytics summary response for dashboard.

    Returned by GET /v1/analytics/summary endpoint.
    Contains key metrics for a specified time period.
    """
    start_date: datetime = Field(..., description="Summary period start")
    end_date: datetime = Field(..., description="Summary period end")
    book_id: Optional[str] = Field(None, description="Book ID filter (null for all books)")

    # Core metrics
    total_queries: int = Field(..., description="Total number of queries")
    unique_users: int = Field(..., description="Number of unique users")

    # Latency metrics (milliseconds)
    latency_p50: int = Field(..., description="Median latency (ms)")
    latency_p95: int = Field(..., description="95th percentile latency (ms)")
    latency_p99: int = Field(..., description="99th percentile latency (ms)")

    # Quality metrics
    feedback_rate: float = Field(..., description="Percentage of queries with feedback (0-100)")
    positive_feedback_rate: Optional[float] = Field(None, description="Percentage of feedback that was positive (0-100)")
    average_confidence: float = Field(..., description="Average confidence score (0-1)")

    # ROI metrics
    teacher_time_saved_minutes: int = Field(..., description="Estimated teacher time saved (minutes)")

    # Top topics
    top_topics: List[Dict[str, Any]] = Field(..., description="Top 10 question topics with counts")

    @field_validator('feedback_rate', 'positive_feedback_rate')
    @classmethod
    def validate_percentage(cls, v: Optional[float]) -> Optional[float]:
        """Validate percentage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    @field_validator('average_confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence score is between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-12-01T00:00:00Z",
                "end_date": "2025-12-11T23:59:59Z",
                "book_id": "physical-ai-robotics",
                "total_queries": 1247,
                "unique_users": 387,
                "latency_p50": 1523,
                "latency_p95": 2847,
                "latency_p99": 3456,
                "feedback_rate": 34.5,
                "positive_feedback_rate": 87.2,
                "average_confidence": 0.82,
                "teacher_time_saved_minutes": 3118,
                "top_topics": [
                    {"topic": "Intelligent Tutoring Systems", "count": 145},
                    {"topic": "Adaptive Feedback", "count": 89},
                    {"topic": "Knowledge Retrieval", "count": 76}
                ]
            }
        }


class TopicDistribution(BaseModel):
    """Topic distribution data for analytics."""
    topic: str = Field(..., description="Topic or keyword")
    count: int = Field(..., description="Number of queries for this topic")
    percentage: Optional[float] = Field(None, description="Percentage of total queries")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Intelligent Tutoring Systems",
                "count": 145,
                "percentage": 11.6
            }
        }


class DailyMetric(BaseModel):
    """Daily metric for trend analysis."""
    date: datetime = Field(..., description="Date for this metric")
    value: float = Field(..., description="Metric value for the day")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-11T00:00:00Z",
                "value": 127
            }
        }
