#!/usr/bin/env python3
"""
Reset Qdrant collection by deleting and recreating it with correct dimensions.

This script is needed when the vector dimensions change (e.g., switching embedding models).

Usage:
    python reset_collection.py [--collection <name>] [--confirm]

Example:
    python reset_collection.py --collection book_chunks_v1 --confirm
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.qdrant import qdrant_client
from src.models.config import settings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset Qdrant collection (delete and recreate with correct dimensions)"
    )
    parser.add_argument(
        "--collection",
        default=None,
        help=f"Collection name to reset (default: {settings.qdrant_collection_name})"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion (required to prevent accidental deletion)"
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=1024,
        help="Vector dimension size (default: 1024 for Cohere embed-english-v3.0)"
    )

    args = parser.parse_args()

    collection_name = args.collection or settings.qdrant_collection_name

    # Require confirmation
    if not args.confirm:
        print("⚠️  WARNING: This will DELETE all data in the collection!", file=sys.stderr)
        print(f"⚠️  Collection: {collection_name}", file=sys.stderr)
        print("", file=sys.stderr)
        print("To confirm, run with --confirm flag:", file=sys.stderr)
        print(f"  python reset_collection.py --collection {collection_name} --confirm", file=sys.stderr)
        sys.exit(1)

    # Connect to Qdrant
    print(f"Connecting to Qdrant at {settings.qdrant_url}...", file=sys.stderr)
    try:
        qdrant_client.connect()
        print("✓ Connected to Qdrant", file=sys.stderr)
    except Exception as e:
        print(f"✗ Failed to connect: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)

    # Check if collection exists
    try:
        collections = qdrant_client.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            print(f"Collection '{collection_name}' does not exist", file=sys.stderr)
            print("Nothing to delete", file=sys.stderr)
        else:
            # Get collection info
            collection_info = qdrant_client.client.get_collection(collection_name)
            vector_size = collection_info.config.params.vectors.size
            points_count = collection_info.points_count

            print(f"Current collection info:", file=sys.stderr)
            print(f"  Name: {collection_name}", file=sys.stderr)
            print(f"  Vector size: {vector_size}", file=sys.stderr)
            print(f"  Points count: {points_count}", file=sys.stderr)
            print("", file=sys.stderr)

            # Delete collection
            print(f"Deleting collection '{collection_name}'...", file=sys.stderr)
            qdrant_client.client.delete_collection(collection_name)
            print(f"✓ Collection deleted", file=sys.stderr)

    except Exception as e:
        print(f"✗ Failed to delete collection: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)

    # Recreate collection with correct dimensions
    print(f"Creating new collection with vector_size={args.vector_size}...", file=sys.stderr)
    try:
        qdrant_client.collection_name = collection_name
        qdrant_client.ensure_collection(vector_size=args.vector_size)
        print(f"✓ Collection recreated: {collection_name}", file=sys.stderr)
        print("", file=sys.stderr)
        print("✓ Reset complete!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Next steps:", file=sys.stderr)
        print("  1. Re-chunk your book content:", file=sys.stderr)
        print("     python scripts/chunk_book.py <book_dir> --output chunks.json", file=sys.stderr)
        print("  2. Generate embeddings and upload:", file=sys.stderr)
        print("     python scripts/embed_chunks.py chunks.json", file=sys.stderr)

    except Exception as e:
        print(f"✗ Failed to recreate collection: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        qdrant_client.close()


if __name__ == "__main__":
    main()
