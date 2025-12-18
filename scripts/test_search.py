#!/usr/bin/env python3
"""
Test Qdrant search functionality.

Usage:
    python test_search.py "query text"
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.qdrant import qdrant_client
from src.services.embedding import embedding_service
from src.models.config import settings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Qdrant search")
    parser.add_argument(
        "query",
        nargs="?",
        default="What is Physical AI",
        help="Search query"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score (0.0 to 1.0)"
    )

    args = parser.parse_args()

    # Connect to Qdrant
    print(f"Connecting to Qdrant...", file=sys.stderr)
    try:
        qdrant_client.connect()
        print(f"✓ Connected to collection: {qdrant_client.collection_name}", file=sys.stderr)
    except Exception as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Get collection info
    try:
        collection_info = qdrant_client.client.get_collection(qdrant_client.collection_name)
        print(f"✓ Collection has {collection_info.points_count} points", file=sys.stderr)
        print("", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not get collection info: {e}", file=sys.stderr)
        print("", file=sys.stderr)

    # Generate query embedding
    print(f"Query: {args.query}", file=sys.stderr)
    print("Generating query embedding...", file=sys.stderr)
    try:
        query_embedding = embedding_service.embed_text(args.query)
        print(f"✓ Embedding generated (dim: {len(query_embedding)})", file=sys.stderr)
    except Exception as e:
        print(f"✗ Embedding failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)

    # Search Qdrant
    print(f"Searching (top_k={args.top_k}, threshold={args.threshold})...", file=sys.stderr)
    try:
        results = qdrant_client.search(
            query_vector=query_embedding,
            top_k=args.top_k,
            score_threshold=args.threshold
        )
        print(f"✓ Found {len(results)} results", file=sys.stderr)
        print("", file=sys.stderr)

        # Display results
        for i, result in enumerate(results, 1):
            print(f"Result {i}:", file=sys.stderr)
            print(f"  Score: {result['score']:.4f}", file=sys.stderr)
            print(f"  Book ID: {result['payload'].get('book_id', 'N/A')}", file=sys.stderr)
            print(f"  Chapter: {result['payload'].get('chapter_number', 'N/A')}", file=sys.stderr)

            content = result['payload'].get('content', '')
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  Content: {preview}", file=sys.stderr)
            print("", file=sys.stderr)

        if not results:
            print("No results found. Try:", file=sys.stderr)
            print("  - Lowering the threshold (--threshold 0.0)", file=sys.stderr)
            print("  - Different query terms", file=sys.stderr)

    except Exception as e:
        print(f"✗ Search failed: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        qdrant_client.close()


if __name__ == "__main__":
    main()
