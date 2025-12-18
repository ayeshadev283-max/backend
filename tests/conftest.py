"""Pytest configuration and shared fixtures for all tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import os
import sys

# Add backend src to Python path
backend_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, backend_path)


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    # Import app after path is set
    from src.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Mock(
        openai_api_key="sk-test-key",
        openai_embedding_model="text-embedding-3-small",
        openai_generation_model="gpt-4o-mini",
        qdrant_url="https://test-qdrant.io",
        qdrant_api_key="test-qdrant-key",
        qdrant_collection_name="test_book_chunks",
        database_url="postgresql://test:test@localhost/test_db",
        similarity_threshold=0.7,
        top_k_retrieval=5,
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests to prevent state leakage."""
    yield
    # Add cleanup code here if using singletons


@pytest.fixture
def sample_book_context():
    """Sample book context for testing."""
    return {
        "book_id": "physical-ai-robotics",
        "title": "Introduction to Physical AI & Humanoid Robotics",
        "version": "1.0"
    }


@pytest.fixture
def sample_chunk_payload():
    """Sample chunk payload structure."""
    return {
        "text": "Zero Moment Point (ZMP) is a fundamental concept in humanoid robotics used for balance control.",
        "chapter": "Module 0 - Foundations",
        "section": "Locomotion and Motor Control",
        "section_slug": "locomotion-motor-control",
        "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md",
        "word_count": 15
    }
