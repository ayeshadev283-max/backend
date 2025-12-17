"""Contract tests for POST /v1/query API endpoint.

Tests verify that request/response schemas match specification and API contracts.
Following TDD: These tests should FAIL until implementation is complete.
"""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID


@pytest.fixture
def valid_query_request():
    """Valid query request payload."""
    return {
        "query_text": "What is Zero Moment Point used for in humanoid robotics?",
        "book_context": {
            "book_id": "physical-ai-robotics",
            "title": "Introduction to Physical AI & Humanoid Robotics",
            "version": "1.0"
        }
    }


@pytest.fixture
def invalid_query_short():
    """Invalid query - too short."""
    return {
        "query_text": "ZMP?",  # Less than 10 characters
        "book_context": {
            "book_id": "physical-ai-robotics",
            "title": "Introduction to Physical AI & Humanoid Robotics",
            "version": "1.0"
        }
    }


@pytest.fixture
def invalid_query_long():
    """Invalid query - too long."""
    return {
        "query_text": "A" * 501,  # More than 500 characters
        "book_context": {
            "book_id": "physical-ai-robotics",
            "title": "Introduction to Physical AI & Humanoid Robotics",
            "version": "1.0"
        }
    }


@pytest.fixture
def invalid_query_missing_context():
    """Invalid query - missing book_context."""
    return {
        "query_text": "What is Zero Moment Point?"
    }


class TestQueryAPIContract:
    """Contract tests for POST /v1/query endpoint."""

    def test_valid_query_returns_200(self, client: TestClient, valid_query_request):
        """Test that valid query returns 200 OK with proper response structure."""
        response = client.post("/v1/query", json=valid_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "response_id" in data
        assert "query_id" in data
        assert "response_text" in data
        assert "source_references" in data
        assert "latency_ms" in data
        assert "timestamp" in data

        # Verify data types
        assert isinstance(UUID(data["response_id"]), UUID)
        assert isinstance(UUID(data["query_id"]), UUID)
        assert isinstance(data["response_text"], str)
        assert isinstance(data["source_references"], list)
        assert isinstance(data["latency_ms"], int)

        # Verify response constraints
        assert len(data["response_text"]) >= 50  # Non-trivial response
        assert len(data["response_text"]) <= 2000  # Within limit
        assert len(data["source_references"]) > 0  # Must have citations

    def test_valid_query_includes_citations(self, client: TestClient, valid_query_request):
        """Test that response includes proper citation structure."""
        response = client.post("/v1/query", json=valid_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify citation structure
        assert "source_references" in data
        citations = data["source_references"]

        assert len(citations) > 0, "Response must include at least one citation"

        for citation in citations:
            assert "chapter" in citation
            assert "section" in citation
            assert "url" in citation
            assert citation["url"].startswith("/chapters/")  # Docusaurus URL format

    def test_query_too_short_returns_422(self, client: TestClient, invalid_query_short):
        """Test that query shorter than 10 characters returns validation error."""
        response = client.post("/v1/query", json=invalid_query_short)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data or "detail" in data
        # Verify error message mentions length constraint

    def test_query_too_long_returns_422(self, client: TestClient, invalid_query_long):
        """Test that query longer than 500 characters returns validation error."""
        response = client.post("/v1/query", json=invalid_query_long)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data or "detail" in data

    def test_missing_book_context_returns_422(self, client: TestClient, invalid_query_missing_context):
        """Test that missing book_context returns validation error."""
        response = client.post("/v1/query", json=invalid_query_missing_context)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data or "detail" in data

    def test_out_of_scope_query_returns_refusal(self, client: TestClient):
        """Test that out-of-scope query returns refusal response."""
        out_of_scope_query = {
            "query_text": "What is the weather in San Francisco today?",  # Not in book
            "book_context": {
                "book_id": "physical-ai-robotics",
                "title": "Introduction to Physical AI & Humanoid Robotics",
                "version": "1.0"
            }
        }

        response = client.post("/v1/query", json=out_of_scope_query)

        assert response.status_code == 200  # Not an error, just refusal
        data = response.json()

        # Verify refusal response structure
        assert "response_text" in data
        assert "refusal_triggered" in data or data["response_text"].startswith("I don't have information")

    def test_response_includes_latency(self, client: TestClient, valid_query_request):
        """Test that response includes latency measurement."""
        response = client.post("/v1/query", json=valid_query_request)

        assert response.status_code == 200
        data = response.json()

        assert "latency_ms" in data
        assert data["latency_ms"] > 0  # Positive latency
        assert data["latency_ms"] < 10000  # Less than 10 seconds

    def test_response_includes_confidence_score(self, client: TestClient, valid_query_request):
        """Test that response includes confidence score (optional field)."""
        response = client.post("/v1/query", json=valid_query_request)

        assert response.status_code == 200
        data = response.json()

        # Confidence score is optional, but if present must be 0.0-1.0
        if "confidence_score" in data:
            assert 0.0 <= data["confidence_score"] <= 1.0

    def test_concurrent_queries_handled(self, client: TestClient, valid_query_request):
        """Test that multiple concurrent queries are handled correctly."""
        import concurrent.futures

        def make_request():
            return client.post("/v1/query", json=valid_query_request)

        # Send 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should have unique response IDs
        response_ids = [r.json()["response_id"] for r in responses]
        assert len(set(response_ids)) == 5  # All unique
