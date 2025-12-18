"""Query and response data models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID, uuid4


class BookContext(BaseModel):
    """Book context information."""

    book_id: str
    chapter_number: Optional[int] = None
    page_url: Optional[str] = None


class QueryRequest(BaseModel):
    """User query request."""

    query: str = Field(..., min_length=1, max_length=500)
    selected_text: Optional[str] = Field(None, max_length=1000)
    book_context: BookContext

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or just whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How much do test scores improve with ITS?",
                "selected_text": "students using ITS achieved 10–15% higher test scores",
                "book_context": {
                    "book_id": "physical-ai-robotics",
                    "chapter_number": 2,
                    "page_url": "/docs/chapters/02-key-ai-applications"
                }
            }
        }


class Query(BaseModel):
    """Query stored in database."""

    query_id: UUID = Field(default_factory=uuid4)
    user_id: str  # SHA-256 hash
    query_text: str
    query_embedding: List[float]
    selected_text: Optional[str] = None
    book_context: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[UUID] = None
    ip_address_hash: Optional[str] = None


class SourceReference(BaseModel):
    """Source reference for a response."""

    chapter: str
    section: Optional[str] = None
    citation: str
    chunk_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "chapter": "2",
                "section": "2.1 Intelligent Tutoring Systems (ITS)",
                "citation": "Chapter 2, Section 2.1",
                "chunk_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class GenerationParams(BaseModel):
    """Parameters used for response generation."""

    model: str
    temperature: float
    max_tokens: int
    system_prompt_version: str
    prompt_token_count: int
    completion_token_count: int


class QueryResponse(BaseModel):
    """Response to a user query."""

    query_id: UUID
    response_text: str = Field(..., min_length=50, max_length=2000)
    source_references: List[SourceReference]
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "7f3d5e2a-1b4c-4f8e-9a3d-6c8b2e4a9f1d",
                "response_text": "Students using Intelligent Tutoring Systems (ITS) achieved 10-15% higher test scores according to research by Pane et al. (2017)...",
                "source_references": [
                    {
                        "chapter": "2",
                        "section": "2.1 Intelligent Tutoring Systems (ITS)",
                        "citation": "Chapter 2, Section 2.1",
                        "chunk_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "confidence_score": 0.85,
                "latency_ms": 1847,
                "timestamp": "2025-12-11T14:25:33Z"
            }
        }


class RetrievedContext(BaseModel):
    """Retrieved context for a query."""

    context_id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    chunk_ids: List[UUID] = Field(..., min_length=1, max_length=10)
    similarity_scores: List[float] = Field(..., min_length=1, max_length=10)
    retrieval_params: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('similarity_scores')
    @classmethod
    def validate_scores_length(cls, v: List[float], info) -> List[float]:
        """Ensure similarity_scores matches chunk_ids length."""
        if 'chunk_ids' in info.data and len(v) != len(info.data['chunk_ids']):
            raise ValueError("similarity_scores must match chunk_ids length")
        return v


class ResponseRecord(BaseModel):
    """Complete response record for database storage."""

    response_id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    response_text: str
    source_references: List[Dict[str, Any]]
    generation_params: Dict[str, Any]
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: Optional[float] = None
