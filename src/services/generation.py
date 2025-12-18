"""Response generation service with Google Gemini integration."""
import logging
import time
from typing import List, Dict, Any
from google import genai

from ..models.config import settings
from ..config.prompts import format_system_prompt, format_retrieved_chunks

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating grounded responses using Google Gemini."""

    def __init__(self):
        """Initialize Google Gemini client."""
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model_name = settings.google_generation_model
        self.max_tokens = settings.google_max_tokens
        self.temperature = settings.google_temperature
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = None

    def generate_response(
        self,
        user_query: str,
        retrieved_chunks: List[Dict[str, Any]],
        book_title: str = "this educational book",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a grounded response from retrieved chunks.

        Args:
            user_query: User's question
            retrieved_chunks: List of retrieved chunks with payload
            book_title: Title of the book
            max_retries: Maximum retry attempts

        Returns:
            Dict with response_text, generation_params, and metadata
        """
        # Check circuit breaker
        if self._is_circuit_broken():
            raise Exception(
                "Circuit breaker open: Too many consecutive failures. "
                "Please try again later."
            )

        # Check if we have sufficient context
        if not retrieved_chunks:
            return self._generate_insufficient_context_response()

        # Format context from chunks
        formatted_chunks = format_retrieved_chunks(retrieved_chunks)

        # Create system prompt
        system_prompt = format_system_prompt(
            book_title=book_title,
            retrieved_chunks=formatted_chunks,
            user_query=user_query
        )

        # Combine system prompt and user query for Gemini
        full_prompt = f"{system_prompt}\n\nUser Question: {user_query}"

        # Generate response with retries
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_tokens,
                    }
                )

                latency_ms = int((time.time() - start_time) * 1000)

                # Extract response text
                response_text = response.text.strip()

                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0

                # Build generation params
                generation_params = {
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "system_prompt_version": "v1.0",
                    "prompt_token_count": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_token_count": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
                }

                total_tokens = generation_params["prompt_token_count"] + generation_params["completion_token_count"]

                logger.info(
                    f"Generated response "
                    f"(latency: {latency_ms}ms, "
                    f"tokens: {total_tokens})"
                )

                return {
                    "response_text": response_text,
                    "generation_params": generation_params,
                    "latency_ms": latency_ms
                }

            except Exception as e:
                error_str = str(e)

                if "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Rate limit hit, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        self._increment_circuit_breaker()
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
                        self._increment_circuit_breaker()
                        logger.error(f"API error after {max_retries} attempts: {e}")
                        raise

        # Should not reach here
        return self._generate_error_response()

    def _generate_insufficient_context_response(self) -> Dict[str, Any]:
        """Generate response when no context is available."""
        response_text = (
            "I don't have enough information in the retrieved sections to answer "
            "this question accurately. Could you try rephrasing or asking about a "
            "topic covered in the book?"
        )

        return {
            "response_text": response_text,
            "generation_params": {
                "model": "fallback",
                "temperature": 0.0,
                "max_tokens": 0,
                "system_prompt_version": "v1.0",
                "prompt_token_count": 0,
                "completion_token_count": 0
            },
            "latency_ms": 0
        }

    def _generate_error_response(self) -> Dict[str, Any]:
        """Generate response when an error occurs."""
        response_text = (
            "I apologize, but I encountered an error while processing your question. "
            "Please try again in a moment."
        )

        return {
            "response_text": response_text,
            "generation_params": {
                "model": "error",
                "temperature": 0.0,
                "max_tokens": 0,
                "system_prompt_version": "v1.0",
                "prompt_token_count": 0,
                "completion_token_count": 0
            },
            "latency_ms": 0
        }

    def _is_circuit_broken(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            # Check if enough time has passed to reset
            if self.circuit_breaker_reset_time:
                if time.time() >= self.circuit_breaker_reset_time:
                    self.circuit_breaker_failures = 0
                    self.circuit_breaker_reset_time = None
                    logger.info("Circuit breaker reset")
                    return False

            return True

        return False

    def _increment_circuit_breaker(self):
        """Increment circuit breaker failure count."""
        self.circuit_breaker_failures += 1

        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            # Set reset time to 60 seconds from now
            self.circuit_breaker_reset_time = time.time() + 60
            logger.warning(
                f"Circuit breaker opened after {self.circuit_breaker_failures} failures. "
                f"Will reset in 60 seconds."
            )


# Global generation service instance
generation_service = GenerationService()
