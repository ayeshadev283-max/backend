#!/usr/bin/env python3
"""
Simple script to reset Qdrant collection (works around version compatibility issues).

Usage:
    python reset_collection_simple.py --confirm
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.models.config import settings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset Qdrant collection"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion (required)"
    )

    args = parser.parse_args()

    collection_name = settings.qdrant_collection_name

    # Require confirmation
    if not args.confirm:
        print("⚠️  WARNING: This will DELETE all data in the collection!", file=sys.stderr)
        print(f"⚠️  Collection: {collection_name}", file=sys.stderr)
        print("", file=sys.stderr)
        print("To confirm, run:", file=sys.stderr)
        print(f"  python scripts/reset_collection_simple.py --confirm", file=sys.stderr)
        sys.exit(1)

    # Connect to Qdrant
    print(f"Connecting to Qdrant...", file=sys.stderr)
    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
            timeout=30.0
        )
        print("✓ Connected", file=sys.stderr)
    except Exception as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)

    # Try to delete collection (ignore if doesn't exist)
    try:
        print(f"Deleting collection '{collection_name}'...", file=sys.stderr)
        result = client.delete_collection(collection_name)
        print(f"✓ Collection deleted", file=sys.stderr)
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "doesn't exist" in error_msg:
            print(f"Collection doesn't exist (already deleted or never created)", file=sys.stderr)
        else:
            print(f"✗ Delete failed: {e}", file=sys.stderr)
            sys.exit(1)

    print("", file=sys.stderr)

    # Create new collection with correct dimensions
    print(f"Creating new collection with 1024 dimensions...", file=sys.stderr)
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1024,  # Cohere embed-english-v3.0
                distance=Distance.COSINE
            )
        )
        print(f"✓ Collection created: {collection_name}", file=sys.stderr)

        # Create payload index for book_id
        from qdrant_client.models import PayloadSchemaType
        client.create_payload_index(
            collection_name=collection_name,
            field_name="book_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print(f"✓ Payload index created", file=sys.stderr)

    except Exception as e:
        print(f"✗ Creation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)
    print("✓ Reset complete!", file=sys.stderr)
    print("", file=sys.stderr)
    print("Next steps:", file=sys.stderr)
    print("  1. Chunk book content:", file=sys.stderr)
    print("     python scripts/chunk_book.py ../docs/chapters --output chunks.json", file=sys.stderr)
    print("  2. Generate embeddings and upload:", file=sys.stderr)
    print("     python scripts/embed_chunks.py chunks.json", file=sys.stderr)

    client.close()


if __name__ == "__main__":
    main()
