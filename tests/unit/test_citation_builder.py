"""Unit tests for CitationBuilder service.

Tests verify citation consolidation and URL generation logic.
Following TDD: These tests should FAIL until implementation is complete.
"""
import pytest
from uuid import uuid4


class TestCitationBuilder:
    """Unit tests for CitationBuilder service."""

    def test_build_citations_consolidates_same_section(self):
        """Test that multiple chunks from same section are merged into single citation."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        # Multiple chunks from same section
        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "ZMP is a fundamental concept...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Locomotion and Motor Control",
                    "section_slug": "locomotion-motor-control",
                    "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
                }
            },
            {
                "id": str(uuid4()),
                "score": 0.78,
                "payload": {
                    "text": "ZMP is used for dynamic balance...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Locomotion and Motor Control",
                    "section_slug": "locomotion-motor-control",
                    "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        # Should consolidate to single citation
        assert len(citations) == 1
        assert citations[0]["chapter"] == "Module 0 - Foundations"
        assert citations[0]["section"] == "Locomotion and Motor Control"

    def test_build_citations_generates_docusaurus_urls(self):
        """Test that citations include proper Docusaurus anchor URLs."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "Content...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Locomotion and Motor Control",
                    "section_slug": "locomotion-motor-control",
                    "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        assert len(citations) == 1
        citation = citations[0]

        # Verify URL format
        assert "url" in citation
        assert citation["url"].startswith("/chapters/")
        assert "#" in citation["url"]  # Anchor link
        assert citation["url"].endswith("locomotion-motor-control")  # Section slug

    def test_build_citations_handles_multiple_sections(self):
        """Test that chunks from different sections create separate citations."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "ZMP content...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Locomotion and Motor Control",
                    "section_slug": "locomotion-motor-control",
                    "source_file": "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
                }
            },
            {
                "id": str(uuid4()),
                "score": 0.80,
                "payload": {
                    "text": "Embodied intelligence content...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Embodied Intelligence",
                    "section_slug": "embodied-intelligence",
                    "source_file": "docs/chapters/module-0-foundations/02-embodied-intelligence.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        # Should create separate citations for different sections
        assert len(citations) == 2

        sections = [c["section"] for c in citations]
        assert "Locomotion and Motor Control" in sections
        assert "Embodied Intelligence" in sections

    def test_build_citations_orders_by_chapter_then_section(self):
        """Test that citations are ordered by chapter number, then section order."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "Module 1 content...",
                    "chapter": "Module 1 - ROS2",
                    "section": "Core Concepts",
                    "section_slug": "core-concepts",
                    "source_file": "docs/chapters/module-1-ros2/01-core-concepts.md"
                }
            },
            {
                "id": str(uuid4()),
                "score": 0.80,
                "payload": {
                    "text": "Module 0 content...",
                    "chapter": "Module 0 - Foundations",
                    "section": "Locomotion",
                    "section_slug": "locomotion",
                    "source_file": "docs/chapters/module-0-foundations/04-locomotion.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        # Module 0 should come before Module 1
        assert citations[0]["chapter"].startswith("Module 0")
        assert citations[1]["chapter"].startswith("Module 1")

    def test_build_citations_includes_chunk_count(self):
        """Test that consolidated citations include count of merged chunks."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        # 3 chunks from same section
        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "Content 1...",
                    "chapter": "Module 0",
                    "section": "Locomotion",
                    "section_slug": "locomotion",
                    "source_file": "docs/chapters/module-0/locomotion.md"
                }
            },
            {
                "id": str(uuid4()),
                "score": 0.80,
                "payload": {
                    "text": "Content 2...",
                    "chapter": "Module 0",
                    "section": "Locomotion",
                    "section_slug": "locomotion",
                    "source_file": "docs/chapters/module-0/locomotion.md"
                }
            },
            {
                "id": str(uuid4()),
                "score": 0.75,
                "payload": {
                    "text": "Content 3...",
                    "chapter": "Module 0",
                    "section": "Locomotion",
                    "section_slug": "locomotion",
                    "source_file": "docs/chapters/module-0/locomotion.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        assert len(citations) == 1
        # Citation should indicate it's from multiple chunks
        assert "chunk_count" in citations[0] or len(citations[0].get("chunk_ids", [])) == 3

    def test_build_citations_handles_empty_chunks(self):
        """Test that empty chunks list returns empty citations."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        citations = citation_builder.build_citations([])

        assert citations == []

    def test_build_citations_handles_missing_metadata(self):
        """Test graceful handling of chunks with missing metadata fields."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        # Chunk with minimal metadata
        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "Content...",
                    # Missing chapter, section, section_slug
                }
            }
        ]

        # Should not crash, may use defaults or skip
        citations = citation_builder.build_citations(chunks)

        # Verify it doesn't crash
        assert isinstance(citations, list)

    def test_url_generation_handles_special_characters(self):
        """Test that URL generation properly handles special characters in section names."""
        from backend.src.services.citation_builder import CitationBuilder

        citation_builder = CitationBuilder()

        chunks = [
            {
                "id": str(uuid4()),
                "score": 0.85,
                "payload": {
                    "text": "Content...",
                    "chapter": "Module 0 - Foundations",
                    "section": "ROS 2 & Simulation",  # Special characters
                    "section_slug": "ros-2-simulation",  # Should be URL-safe
                    "source_file": "docs/chapters/module-0/ros2.md"
                }
            }
        ]

        citations = citation_builder.build_citations(chunks)

        assert len(citations) == 1
        # URL should be safe (no spaces, special chars encoded)
        url = citations[0]["url"]
        assert " " not in url
        assert "&" not in url
