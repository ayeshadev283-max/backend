"""
Pydantic models for user feedback data structures.

This module defines data models for user feedback on chatbot responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator


class UserFeedback(BaseModel):
    """
    User feedback on a chatbot response.

    Stores user ratings and optional comments for quality improvement.
    """
    feedback_id: UUID = Field(default_factory=uuid4, description="Unique feedback identifier")
    response_id: UUID = Field(..., description="Associated response ID")
    rating: str = Field(..., description="User rating: 'helpful' or 'not_helpful'")
    comment: Optional[str] = Field(None, description="Optional feedback comment (0-500 chars)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Feedback submission time")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        """Validate rating is 'helpful' or 'not_helpful'."""
        if v not in ('helpful', 'not_helpful'):
            raise ValueError("Rating must be 'helpful' or 'not_helpful'")
        return v

    @field_validator('comment')
    @classmethod
    def validate_comment_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate comment length if present."""
        if v is not None and len(v) > 500:
            raise ValueError("Comment must be 500 characters or less")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "feedback_id": "c3d4e5f6-g7h8-9i0j-1k2l-m3n4o5p6q7r8",
                "response_id": "b2c3d4e5-f6g7-8h9i-0j1k-l2m3n4o5p6q7",
                "rating": "helpful",
                "comment": "This answer was very clear and included the exact citation I needed!",
                "timestamp": "2025-12-11T14:26:15Z"
            }
        }


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    response_id: UUID = Field(..., description="Response ID to provide feedback for")
    rating: str = Field(..., description="Rating: 'helpful' or 'not_helpful'")
    comment: Optional[str] = Field(None, description="Optional comment (max 500 chars)")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: str) -> str:
        """Validate rating is 'helpful' or 'not_helpful'."""
        if v not in ('helpful', 'not_helpful'):
            raise ValueError("Rating must be 'helpful' or 'not_helpful'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "b2c3d4e5-f6g7-8h9i-0j1k-l2m3n4o5p6q7",
                "rating": "helpful",
                "comment": "Great explanation with clear sources!"
            }
        }


class FeedbackResponse(BaseModel):
    """Response model after submitting feedback."""
    feedback_id: UUID = Field(..., description="Created feedback ID")
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(..., description="Submission timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "feedback_id": "c3d4e5f6-g7h8-9i0j-1k2l-m3n4o5p6q7r8",
                "message": "Feedback submitted successfully",
                "timestamp": "2025-12-11T14:26:15Z"
            }
        }
