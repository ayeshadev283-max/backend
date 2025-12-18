"""Citation builder service for consolidating and formatting source references.

Consolidates multiple chunks from the same section into single citations
and generates Docusaurus-compatible URLs.
"""
from typing import List, Dict, Any
from collections import defaultdict
import re


class CitationBuilder:
    """Build and consolidate citations from retrieved chunks."""

    def build_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build consolidated citations from retrieved chunks.

        Consolidates multiple chunks from the same section into a single citation
        and generates Docusaurus anchor URLs.

        Args:
            chunks: List of retrieved chunks with payload containing metadata

        Returns:
            List of citation objects with chapter, section, url, and chunk_count
        """
        if not chunks:
            return []

        # Group chunks by (chapter, section)
        section_groups = defaultdict(list)

        for chunk in chunks:
            payload = chunk.get("payload", {})

            # Extract metadata (with defaults for robustness)
            chapter = payload.get("chapter", "Unknown Chapter")
            section = payload.get("section", "Unknown Section")
            section_slug = payload.get("section_slug", self._generate_slug(section))
            source_file = payload.get("source_file", "")

            # Create unique key for grouping
            section_key = (chapter, section, section_slug, source_file)

            section_groups[section_key].append(chunk)

        # Build citations from groups
        citations = []

        for (chapter, section, section_slug, source_file), group_chunks in section_groups.items():
            # Extract module/topic from source_file for URL
            url = self._build_citation_url(source_file, section_slug)

            citation = {
                "chapter": chapter,
                "section": section,
                "url": url,
                "chunk_count": len(group_chunks),
                "chunk_ids": [chunk.get("id") for chunk in group_chunks],
                "max_similarity": max(chunk.get("score", 0.0) for chunk in group_chunks),
            }

            citations.append(citation)

        # Sort citations by chapter order (extract module number if present)
        citations.sort(key=lambda c: self._extract_chapter_order(c["chapter"]))

        return citations

    def _build_citation_url(self, source_file: str, section_slug: str) -> str:
        """
        Build Docusaurus anchor URL from source file path.

        Args:
            source_file: Path like "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
            section_slug: URL-safe section identifier like "locomotion-motor-control"

        Returns:
            URL like "/chapters/module-0-foundations/locomotion-motor-control#locomotion-motor-control"
        """
        if not source_file:
            return f"#unknown-section"

        # Extract path components
        # Example: "docs/chapters/module-0-foundations/04-locomotion-motor-control.md"
        # -> "/chapters/module-0-foundations/locomotion-motor-control#locomotion-motor-control"

        # Remove file extension and "docs/" prefix
        clean_path = source_file.replace("docs/", "").replace(".md", "")

        # Remove numeric prefixes from filename (e.g., "04-locomotion" -> "locomotion")
        parts = clean_path.split("/")
        if parts:
            filename = parts[-1]
            # Remove leading digits and dash (e.g., "04-name" -> "name")
            filename = re.sub(r"^\d+-", "", filename)
            parts[-1] = filename

        # Reconstruct path
        base_path = "/".join(parts)

        # Add anchor
        return f"/{base_path}#{section_slug}"

    def _generate_slug(self, section: str) -> str:
        """
        Generate URL-safe slug from section name.

        Args:
            section: Section title like "Locomotion and Motor Control"

        Returns:
            Slug like "locomotion-and-motor-control"
        """
        slug = section.lower()
        # Replace spaces and special characters with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        return slug

    def _extract_chapter_order(self, chapter: str) -> tuple:
        """
        Extract chapter ordering for sorting.

        Args:
            chapter: Chapter name like "Module 0 - Foundations" or "Module 1 - ROS2"

        Returns:
            Tuple (module_number, chapter) for sorting
        """
        # Try to extract module number
        match = re.search(r"Module\s+(\d+)", chapter, re.IGNORECASE)
        if match:
            return (int(match.group(1)), chapter)

        # No module number found, sort alphabetically
        return (999, chapter)


# Global citation builder instance
citation_builder = CitationBuilder()
