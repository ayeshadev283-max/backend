"""API response schemas for standardized responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SuccessResponse(BaseModel):
    """Standard success response wrapper."""

    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"response_id": "123e4567-e89b-12d3-a456-426614174000"},
                "message": "Query processed successfully",
                "timestamp": "2025-12-15T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Query text must be between 10 and 500 characters",
                "error_code": "VALIDATION_ERROR",
                "details": {"field": "query_text", "provided_length": 5},
                "timestamp": "2025-12-15T10:30:00Z"
            }
        }


class ValidationError(BaseModel):
    """Validation error detail."""

    field: str
    message: str
    type: str
    value: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "field": "query_text",
                "message": "String should have at least 10 characters",
                "type": "string_too_short",
                "value": "test"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Response for validation errors with multiple fields."""

    success: bool = False
    error: str = "Validation error"
    error_code: str = "VALIDATION_ERROR"
    validation_errors: List[ValidationError]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "validation_errors": [
                    {
                        "field": "query_text",
                        "message": "String should have at least 10 characters",
                        "type": "string_too_short",
                        "value": "test"
                    }
                ],
                "timestamp": "2025-12-15T10:30:00Z"
            }
        }
