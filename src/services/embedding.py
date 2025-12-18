"""Embedding service with Cohere integration."""
import logging
import time
from typing import List
import cohere

from ..models.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Cohere API."""

    def __init__(self):
        """Initialize Cohere client."""
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = settings.cohere_embedding_model

    def embed_text(
        self,
        text: str,
        max_retries: int = 3
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            max_retries: Maximum number of retry attempts

        Returns:
            Embedding vector (1024 dimensions for embed-english-v3.0)
        """
        return self.embed_batch([text], max_retries=max_retries)[0]

    def embed_batch(
        self,
        texts: List[str],
        max_retries: int = 3
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with retry logic.

        Args:
            texts: List of texts to embed
            max_retries: Maximum number of retry attempts

        Returns:
            List of embedding vectors
        """
        for attempt in range(max_retries):
            try:
                # Cohere can process multiple texts at once
                response = self.client.embed(
                    texts=texts,
                    model=self.model,
                    input_type="search_document"  # Use for indexing documents
                )

                embeddings = response.embeddings

                logger.info(
                    f"Generated {len(embeddings)} embeddings "
                    f"(model: {self.model})"
                )

                return embeddings

            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str or "quota" in error_str or "limit" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Rate limit hit, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"API error, retrying in {wait_time}s: {e} "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"API error after {max_retries} attempts: {e}")
                        raise

        # Should not reach here, but return empty list as fallback
        return []

    def embed_chunks(
        self,
        chunks: List[dict],
        batch_size: int = 96  # Cohere allows up to 96 texts per request
    ) -> List[dict]:
        """
        Generate embeddings for list of chunks with batching.

        Args:
            chunks: List of chunk dicts with 'content' key
            batch_size: Number of chunks to embed per batch (max 96 for Cohere)

        Returns:
            List of chunks with 'embedding' added
        """
        total_chunks = len(chunks)
        logger.info(f"Embedding {total_chunks} chunks in batches of {batch_size}")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = [chunk['content'] for chunk in batch]

            try:
                embeddings = self.embed_batch(batch_texts)

                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    chunk['embedding'] = embedding

                logger.info(
                    f"Processed batch {i // batch_size + 1} "
                    f"({i + len(batch)}/{total_chunks} chunks)"
                )

            except Exception as e:
                logger.error(f"Failed to embed batch starting at {i}: {e}")
                raise

        return chunks


# Global embedding service instance
embedding_service = EmbeddingService()
