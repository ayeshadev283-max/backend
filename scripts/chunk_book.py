#!/usr/bin/env python3
"""
Chunk book content from Markdown files.

Usage:
    python chunk_book.py <book_dir> [--book-id <id>] [--version <version>] [--output <file>]

Example:
    python chunk_book.py ../docs/chapters --book-id physical-ai-robotics --version v1.0.0 --output chunks.json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.chunking import chunking_service


def chunk_book_directory(
    book_dir: str,
    book_id: str,
    book_version: str
) -> List[Dict[str, Any]]:
    """
    Process all Markdown files in a directory and chunk them.

    Args:
        book_dir: Path to directory containing Markdown files
        book_id: Book identifier
        book_version: Book version

    Returns:
        List of all chunks from all files
    """
    book_path = Path(book_dir)

    if not book_path.exists():
        raise FileNotFoundError(f"Directory not found: {book_dir}")

    # Find all Markdown files recursively
    md_files = sorted(book_path.glob("**/*.md"))

    if not md_files:
        print(f"Warning: No Markdown files found in {book_dir}", file=sys.stderr)
        return []

    all_chunks = []

    for i, md_file in enumerate(md_files, start=1):
        print(f"Processing {md_file.name}...", file=sys.stderr)

        try:
            chunks = chunking_service.chunk_markdown_file(
                file_path=str(md_file),
                book_id=book_id,
                book_version=book_version,
                chapter_number=i
            )

            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks created", file=sys.stderr)

        except Exception as e:
            print(f"  → Error: {e}", file=sys.stderr)
            continue

    return all_chunks


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Chunk book content from Markdown files"
    )
    parser.add_argument(
        "book_dir",
        help="Path to directory containing Markdown chapter files"
    )
    parser.add_argument(
        "--book-id",
        default="physical-ai-robotics",
        help="Book identifier (default: physical-ai-robotics)"
    )
    parser.add_argument(
        "--version",
        default="v1.0.0",
        help="Book version (default: v1.0.0)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file (default: stdout)"
    )

    args = parser.parse_args()

    # Chunk the book
    print(f"Chunking book: {args.book_id} {args.version}", file=sys.stderr)
    print(f"Source directory: {args.book_dir}", file=sys.stderr)
    print("", file=sys.stderr)

    chunks = chunk_book_directory(
        book_dir=args.book_dir,
        book_id=args.book_id,
        book_version=args.version
    )

    print("", file=sys.stderr)
    print(f"Total chunks created: {len(chunks)}", file=sys.stderr)

    # Output JSON
    output_data = {
        "book_id": args.book_id,
        "book_version": args.version,
        "total_chunks": len(chunks),
        "chunks": chunks
    }

    json_output = json.dumps(output_data, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output, encoding='utf-8')
        print(f"Output written to: {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
