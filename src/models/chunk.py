"""Book chunk data models."""
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class ChunkMetadata(BaseModel):
    """Metadata for a book content chunk."""

    book_id: str
    book_version: str
    chapter_number: int
    chapter_title: str
    section: str
    subsection: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: int
    word_count: int
    has_code_block: bool = False
    has_math: bool = False
    source_file: str


class BookChunk(BaseModel):
    """Book content chunk with vector embedding."""

    id: UUID
    vector: List[float] = Field(..., min_length=1536, max_length=1536)
    content: str = Field(..., min_length=100, max_length=10000)
    metadata: ChunkMetadata

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "vector": [0.023, -0.015, 0.042],  # Truncated for example
                "content": "Intelligent Tutoring Systems (ITS) are AI-driven platforms...",
                "metadata": {
                    "book_id": "physical-ai-robotics",
                    "book_version": "v1.0.0",
                    "chapter_number": 2,
                    "chapter_title": "Key AI Applications in K-12 Education",
                    "section": "2.1 Intelligent Tutoring Systems (ITS)",
                    "subsection": None,
                    "page_number": 15,
                    "chunk_index": 0,
                    "word_count": 487,
                    "has_code_block": False,
                    "has_math": False,
                    "source_file": "02-key-ai-applications.md"
                }
            }
        }
