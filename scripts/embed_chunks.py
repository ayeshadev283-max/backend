#!/usr/bin/env python3
"""
Generate embeddings for chunks and upload to Qdrant.

Usage:
    python embed_chunks.py <chunks_file> [--collection <name>] [--batch-size <n>]

Example:
    python embed_chunks.py chunks.json --collection book_chunks_v1 --batch-size 100
"""
import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.embedding import embedding_service
from src.db.qdrant import qdrant_client


def load_chunks_file(file_path: str) -> Dict[str, Any]:
    """
    Load chunks from JSON file.

    Args:
        file_path: Path to chunks JSON file

    Returns:
        Dict with book_id, book_version, and chunks list
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'chunks' not in data:
        raise ValueError("Invalid chunks file: missing 'chunks' key")

    return data


def prepare_chunks_for_qdrant(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Prepare chunks for Qdrant upload.

    Args:
        chunks: List of chunks with 'embedding' and 'metadata'

    Returns:
        List of dicts with 'id', 'vector', and 'payload' for Qdrant
    """
    qdrant_chunks = []

    for chunk in chunks:
        if 'embedding' not in chunk:
            print(
                f"Warning: Chunk missing embedding, skipping",
                file=sys.stderr
            )
            continue

        # Create payload with metadata and content
        payload = chunk.get('metadata', {}).copy()
        payload['content'] = chunk['content']

        qdrant_chunk = {
            "id": str(uuid.uuid4()),
            "vector": chunk['embedding'],
            "payload": payload
        }

        qdrant_chunks.append(qdrant_chunk)

    return qdrant_chunks


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings and upload to Qdrant"
    )
    parser.add_argument(
        "chunks_file",
        help="Path to chunks JSON file (from chunk_book.py)"
    )
    parser.add_argument(
        "--collection",
        help="Qdrant collection name (default: from settings)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Embedding batch size (default: 100)"
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Skip embedding generation (chunks already have embeddings)"
    )

    args = parser.parse_args()

    # Load chunks file
    print(f"Loading chunks from: {args.chunks_file}", file=sys.stderr)
    data = load_chunks_file(args.chunks_file)

    book_id = data.get('book_id', 'unknown')
    book_version = data.get('book_version', 'unknown')
    chunks = data['chunks']

    print(f"Book: {book_id} {book_version}", file=sys.stderr)
    print(f"Total chunks: {len(chunks)}", file=sys.stderr)
    print("", file=sys.stderr)

    # Generate embeddings if needed
    if not args.skip_embedding:
        print("Generating embeddings...", file=sys.stderr)
        try:
            chunks = embedding_service.embed_chunks(
                chunks,
                batch_size=args.batch_size
            )
            print(f"✓ Embeddings generated for {len(chunks)} chunks", file=sys.stderr)
        except Exception as e:
            print(f"✗ Embedding generation failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Skipping embedding generation", file=sys.stderr)

    print("", file=sys.stderr)

    # Connect to Qdrant
    print("Connecting to Qdrant...", file=sys.stderr)
    try:
        qdrant_client.connect()

        # Set collection name if specified
        if args.collection:
            qdrant_client.collection_name = args.collection

        # Ensure collection exists (1024 for Cohere embed-english-v3.0)
        qdrant_client.ensure_collection(vector_size=1024)

        print(f"✓ Connected to collection: {qdrant_client.collection_name}", file=sys.stderr)

    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("", file=sys.stderr)

    # Prepare chunks for Qdrant
    print("Preparing chunks for upload...", file=sys.stderr)
    qdrant_chunks = prepare_chunks_for_qdrant(chunks)
    print(f"✓ {len(qdrant_chunks)} chunks ready for upload", file=sys.stderr)

    # Upload to Qdrant in batches
    print("", file=sys.stderr)
    print(f"Uploading chunks to Qdrant...", file=sys.stderr)

    batch_size = 500  # Qdrant batch size
    total_uploaded = 0

    try:
        for i in range(0, len(qdrant_chunks), batch_size):
            batch = qdrant_chunks[i:i + batch_size]
            qdrant_client.upsert_chunks(batch)

            total_uploaded += len(batch)
            print(
                f"  → Uploaded {total_uploaded}/{len(qdrant_chunks)} chunks",
                file=sys.stderr
            )

        print("", file=sys.stderr)
        print(f"✓ Upload complete: {total_uploaded} chunks in {qdrant_client.collection_name}", file=sys.stderr)

    except Exception as e:
        print(f"✗ Upload failed: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        qdrant_client.close()


if __name__ == "__main__":
    main()
