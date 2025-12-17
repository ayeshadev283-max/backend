"""Text chunking service for book content."""
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..models.config import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for chunking Markdown book content into semantically meaningful segments."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target chunk size in words (default from settings)
            chunk_overlap: Overlap between chunks in words (default from settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_markdown_file(
        self,
        file_path: str,
        book_id: str,
        book_version: str,
        chapter_number: int
    ) -> List[Dict[str, Any]]:
        """
        Chunk a Markdown file into segments.

        Args:
            file_path: Path to Markdown file
            book_id: Book identifier
            book_version: Book version
            chapter_number: Chapter number

        Returns:
            List of chunk dictionaries with content and metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract chapter title from first heading
        chapter_title = self._extract_chapter_title(content)

        # Split content into sections
        sections = self._split_into_sections(content)

        # Chunk each section
        chunks = []
        chunk_index = 0

        for section_title, section_content in sections:
            section_chunks = self._chunk_text(
                section_content,
                max_words=self.chunk_size,
                overlap_words=self.chunk_overlap
            )

            for chunk_text in section_chunks:
                # Count words
                word_count = len(chunk_text.split())

                # Check for code blocks and math
                has_code_block = '```' in chunk_text
                has_math = '$' in chunk_text or '$$' in chunk_text

                chunk = {
                    "content": chunk_text,
                    "metadata": {
                        "book_id": book_id,
                        "book_version": book_version,
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title,
                        "section": section_title,
                        "subsection": None,
                        "page_number": None,
                        "chunk_index": chunk_index,
                        "word_count": word_count,
                        "has_code_block": has_code_block,
                        "has_math": has_math,
                        "source_file": str(Path(file_path).name)
                    }
                }

                chunks.append(chunk)
                chunk_index += 1

        logger.info(f"Chunked {file_path}: {len(chunks)} chunks created")
        return chunks

    def _extract_chapter_title(self, content: str) -> str:
        """Extract chapter title from first heading."""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else "Unknown Chapter"

    def _split_into_sections(self, content: str) -> List[tuple]:
        """
        Split content into sections based on headings.

        Returns:
            List of (section_title, section_content) tuples
        """
        sections = []

        # Split by H2 headings (##)
        section_pattern = r'^##\s+(.+)$'
        matches = list(re.finditer(section_pattern, content, re.MULTILINE))

        if not matches:
            # No sections found, treat entire content as one section
            return [("Main Content", content)]

        # First section (before first H2)
        if matches[0].start() > 0:
            intro_content = content[:matches[0].start()].strip()
            if intro_content:
                sections.append(("Introduction", intro_content))

        # Process each section
        for i, match in enumerate(matches):
            section_title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            section_content = content[start:end].strip()
            if section_content:
                sections.append((section_title, section_content))

        return sections

    def _chunk_text(
        self,
        text: str,
        max_words: int,
        overlap_words: int
    ) -> List[str]:
        """
        Chunk text into segments with overlap.

        Args:
            text: Text to chunk
            max_words: Maximum words per chunk
            overlap_words: Overlap between chunks in words

        Returns:
            List of text chunks
        """
        # Preserve code blocks
        code_blocks = []
        text_with_placeholders = text

        # Extract code blocks
        code_pattern = r'```[\s\S]*?```'
        for i, match in enumerate(re.finditer(code_pattern, text)):
            placeholder = f"__CODE_BLOCK_{i}__"
            code_blocks.append(match.group(0))
            text_with_placeholders = text_with_placeholders.replace(
                match.group(0),
                placeholder,
                1
            )

        # Split into paragraphs
        paragraphs = [p.strip() for p in text_with_placeholders.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = []
        current_word_count = 0

        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())

            # If single paragraph exceeds max_words, keep it as one chunk
            if paragraph_words > max_words and not current_chunk:
                chunks.append(paragraph)
                continue

            # If adding this paragraph exceeds max_words, finalize current chunk
            if current_word_count + paragraph_words > max_words and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_paragraphs = self._get_overlap_paragraphs(
                    current_chunk,
                    overlap_words
                )
                current_chunk = overlap_paragraphs + [paragraph]
                current_word_count = sum(len(p.split()) for p in current_chunk)
            else:
                current_chunk.append(paragraph)
                current_word_count += paragraph_words

        # Add remaining chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)

        # Restore code blocks
        final_chunks = []
        for chunk in chunks:
            for i, code_block in enumerate(code_blocks):
                chunk = chunk.replace(f"__CODE_BLOCK_{i}__", code_block)
            final_chunks.append(chunk)

        return final_chunks

    def _get_overlap_paragraphs(
        self,
        paragraphs: List[str],
        overlap_words: int
    ) -> List[str]:
        """Get paragraphs for overlap from end of chunk."""
        overlap_paragraphs = []
        word_count = 0

        for paragraph in reversed(paragraphs):
            paragraph_words = len(paragraph.split())
            if word_count + paragraph_words <= overlap_words:
                overlap_paragraphs.insert(0, paragraph)
                word_count += paragraph_words
            else:
                break

        return overlap_paragraphs


# Global chunking service instance
chunking_service = ChunkingService()
