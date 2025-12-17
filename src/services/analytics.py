"""
Analytics service for computing chatbot usage metrics.

This service provides methods for:
- Calculating query counts and user engagement
- Computing latency percentiles
- Extracting topic distributions
- Estimating ROI (teacher time saved)
- Aggregating daily/weekly/monthly metrics
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.postgres import get_session
from ..models.analytics import AnalyticsSummary, TopicDistribution, AnalyticsAggregate


class AnalyticsService:
    """Service for computing and aggregating analytics metrics."""

    def __init__(self):
        """Initialize analytics service."""
        # Minutes saved per query (average teacher intervention time)
        self.minutes_per_query = 2.5

    async def calculate_query_count(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Calculate total queries and unique users.

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter

        Returns:
            Tuple of (total_queries, unique_users)
        """
        async with get_session() as session:
            # Build query
            from ..models.query import Query

            query = select(
                func.count(Query.query_id).label('total_queries'),
                func.count(func.distinct(Query.user_id)).label('unique_users')
            ).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date
                )
            )

            # Add book filter if specified
            if book_id:
                query = query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            result = await session.execute(query)
            row = result.first()

            return (row.total_queries or 0, row.unique_users or 0)

    async def calculate_latency_percentiles(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None
    ) -> Tuple[int, int, int]:
        """
        Calculate latency percentiles (p50, p95, p99).

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter

        Returns:
            Tuple of (p50_ms, p95_ms, p99_ms)
        """
        async with get_session() as session:
            from ..models.query import Query, QueryResponse

            # Build query to get all latencies
            query = select(QueryResponse.latency_ms).join(
                Query, Query.query_id == QueryResponse.query_id
            ).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date
                )
            )

            # Add book filter if specified
            if book_id:
                query = query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            result = await session.execute(query)
            latencies = [row[0] for row in result.fetchall()]

            if not latencies:
                return (0, 0, 0)

            # Calculate percentiles
            latencies.sort()
            n = len(latencies)

            p50_idx = int(n * 0.50)
            p95_idx = int(n * 0.95)
            p99_idx = int(n * 0.99)

            return (
                latencies[p50_idx],
                latencies[p95_idx],
                latencies[p99_idx]
            )

    async def calculate_feedback_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None
    ) -> Tuple[float, Optional[float]]:
        """
        Calculate feedback rate and positive feedback rate.

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter

        Returns:
            Tuple of (feedback_rate_percentage, positive_feedback_rate_percentage)
        """
        async with get_session() as session:
            from ..models.query import Query, QueryResponse
            from ..models.feedback import UserFeedback

            # Count total responses
            total_query = select(func.count(QueryResponse.response_id)).join(
                Query, Query.query_id == QueryResponse.query_id
            ).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date
                )
            )

            if book_id:
                total_query = total_query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            total_result = await session.execute(total_query)
            total_responses = total_result.scalar() or 0

            if total_responses == 0:
                return (0.0, None)

            # Count feedbacks
            feedback_query = select(
                func.count(UserFeedback.feedback_id).label('total_feedback'),
                func.sum(
                    func.cast(UserFeedback.rating == 'helpful', int)
                ).label('positive_feedback')
            ).join(
                QueryResponse, QueryResponse.response_id == UserFeedback.response_id
            ).join(
                Query, Query.query_id == QueryResponse.query_id
            ).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date
                )
            )

            if book_id:
                feedback_query = feedback_query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            feedback_result = await session.execute(feedback_query)
            feedback_row = feedback_result.first()

            total_feedback = feedback_row.total_feedback or 0
            positive_feedback = feedback_row.positive_feedback or 0

            # Calculate rates
            feedback_rate = (total_feedback / total_responses) * 100

            positive_rate = None
            if total_feedback > 0:
                positive_rate = (positive_feedback / total_feedback) * 100

            return (feedback_rate, positive_rate)

    async def calculate_average_confidence(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None
    ) -> float:
        """
        Calculate average confidence score.

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter

        Returns:
            Average confidence score (0-1)
        """
        async with get_session() as session:
            from ..models.query import Query, QueryResponse

            query = select(
                func.avg(QueryResponse.confidence_score)
            ).join(
                Query, Query.query_id == QueryResponse.query_id
            ).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date,
                    QueryResponse.confidence_score.isnot(None)
                )
            )

            if book_id:
                query = query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            result = await session.execute(query)
            avg_confidence = result.scalar()

            return float(avg_confidence) if avg_confidence else 0.0

    def calculate_teacher_time_saved(self, total_queries: int) -> int:
        """
        Estimate teacher time saved based on query count.

        Args:
            total_queries: Number of queries handled by chatbot

        Returns:
            Estimated minutes saved
        """
        return int(total_queries * self.minutes_per_query)

    async def extract_top_topics(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract top question topics from query text.

        Uses keyword extraction to identify common topics/themes.

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter
            top_n: Number of top topics to return

        Returns:
            List of topic dictionaries with topic and count
        """
        async with get_session() as session:
            from ..models.query import Query

            # Fetch all query texts
            query = select(Query.query_text).where(
                and_(
                    Query.timestamp >= start_date,
                    Query.timestamp <= end_date
                )
            )

            if book_id:
                query = query.where(
                    Query.book_context['book_id'].astext == book_id
                )

            result = await session.execute(query)
            query_texts = [row[0] for row in result.fetchall()]

            if not query_texts:
                return []

            # Extract keywords/phrases
            topics = self._extract_keywords_from_queries(query_texts)

            # Get top N topics
            topic_counter = Counter(topics)
            top_topics = topic_counter.most_common(top_n)

            return [
                {"topic": topic, "count": count}
                for topic, count in top_topics
            ]

    def _extract_keywords_from_queries(self, queries: List[str]) -> List[str]:
        """
        Extract keywords/topics from query texts.

        Simple keyword extraction using:
        1. Capitalized phrases (likely proper nouns/topics)
        2. Common educational terms
        3. Technical terms from the domain

        Args:
            queries: List of query text strings

        Returns:
            List of extracted keywords
        """
        keywords = []

        # Common stopwords to ignore
        stopwords = {
            'what', 'how', 'why', 'when', 'where', 'who', 'which',
            'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or',
            'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'about', 'as', 'into', 'like', 'through', 'after',
            'over', 'between', 'out', 'against', 'during', 'without',
            'before', 'under', 'around', 'among', 'does', 'do', 'did',
            'can', 'could', 'should', 'would', 'will', 'may', 'might',
            'must', 'shall', 'explain', 'describe', 'tell', 'me', 'you'
        }

        for query in queries:
            # Extract capitalized phrases (2-4 words)
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b', query)
            keywords.extend(capitalized)

            # Extract technical terms (words with 5+ characters not in stopwords)
            words = re.findall(r'\b\w{5,}\b', query.lower())
            keywords.extend([w for w in words if w not in stopwords])

        return keywords

    async def get_analytics_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        book_id: Optional[str] = None
    ) -> AnalyticsSummary:
        """
        Get comprehensive analytics summary for a time period.

        Args:
            start_date: Period start
            end_date: Period end
            book_id: Optional book filter

        Returns:
            AnalyticsSummary with all metrics
        """
        # Run all calculations concurrently
        results = await asyncio.gather(
            self.calculate_query_count(start_date, end_date, book_id),
            self.calculate_latency_percentiles(start_date, end_date, book_id),
            self.calculate_feedback_rate(start_date, end_date, book_id),
            self.calculate_average_confidence(start_date, end_date, book_id),
            self.extract_top_topics(start_date, end_date, book_id)
        )

        total_queries, unique_users = results[0]
        latency_p50, latency_p95, latency_p99 = results[1]
        feedback_rate, positive_feedback_rate = results[2]
        average_confidence = results[3]
        top_topics = results[4]

        # Calculate teacher time saved
        teacher_time_saved = self.calculate_teacher_time_saved(total_queries)

        return AnalyticsSummary(
            start_date=start_date,
            end_date=end_date,
            book_id=book_id,
            total_queries=total_queries,
            unique_users=unique_users,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            feedback_rate=feedback_rate,
            positive_feedback_rate=positive_feedback_rate,
            average_confidence=average_confidence,
            teacher_time_saved_minutes=teacher_time_saved,
            top_topics=top_topics
        )

    async def compute_daily_aggregates(
        self,
        date: datetime,
        book_id: Optional[str] = None
    ) -> List[AnalyticsAggregate]:
        """
        Compute daily aggregates for all metrics.

        This method can be run as a background job/cron task.

        Args:
            date: Date to compute aggregates for
            book_id: Optional book filter

        Returns:
            List of AnalyticsAggregate records
        """
        # Set time bounds for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        aggregates = []

        # 1. Daily query count
        total_queries, unique_users = await self.calculate_query_count(
            start_of_day, end_of_day, book_id
        )
        aggregates.append(AnalyticsAggregate(
            metric_name='daily_query_count',
            time_period_start=start_of_day,
            time_period_end=end_of_day,
            metric_value={
                'total_queries': total_queries,
                'unique_users': unique_users
            },
            book_id=book_id
        ))

        # 2. Daily latency metrics
        if total_queries > 0:
            p50, p95, p99 = await self.calculate_latency_percentiles(
                start_of_day, end_of_day, book_id
            )
            # Note: Using 'weekly_avg_latency' for daily too (metric_name constraint)
            aggregates.append(AnalyticsAggregate(
                metric_name='weekly_avg_latency',
                time_period_start=start_of_day,
                time_period_end=end_of_day,
                metric_value={
                    'p50': p50,
                    'p95': p95,
                    'p99': p99
                },
                book_id=book_id
            ))

            # 3. Top topics
            top_topics = await self.extract_top_topics(
                start_of_day, end_of_day, book_id
            )
            if top_topics:
                aggregates.append(AnalyticsAggregate(
                    metric_name='top_question_topics',
                    time_period_start=start_of_day,
                    time_period_end=end_of_day,
                    metric_value={'topics': top_topics},
                    book_id=book_id
                ))

        return aggregates


# Singleton instance
analytics_service = AnalyticsService()
