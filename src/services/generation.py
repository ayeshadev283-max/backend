"""Response generation service with Cohere integration."""
import logging
import time
from typing import List, Dict, Any
import cohere

from ..models.config import settings
from ..config.prompts import format_system_prompt, format_retrieved_chunks

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating grounded responses using Cohere."""

    def __init__(self):
        """Initialize Cohere client."""
        self.client = cohere.Client(settings.cohere_api_key)
        self.model_name = settings.cohere_generation_model
        self.max_tokens = settings.cohere_max_tokens
        self.temperature = settings.cohere_temperature
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

        # Generate response with retries
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = self.client.chat(
                    model=self.model_name,
                    message=user_query,
                    preamble=system_prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
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
                    "prompt_token_count": response.meta.billed_units.input_tokens if hasattr(response.meta, 'billed_units') else 0,
                    "completion_token_count": response.meta.billed_units.output_tokens if hasattr(response.meta, 'billed_units') else 0
                }

                logger.info(
                    f"Generated response in {latency_ms}ms "
                    f"(model: {self.model_name}, tokens: {generation_params['completion_token_count']})"
                )

                return {
                    "response_text": response_text,
                    "generation_params": generation_params,
                    "latency_ms": latency_ms
                }

            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str or "quota" in error_str or "limit" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Rate limit hit, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        self._increment_circuit_breaker()
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
                        logger.error(f"Generation error after {max_retries} attempts: {e}")
                        self._increment_circuit_breaker()
                        raise

        # Fallback
        return self._generate_error_response()

    def _is_circuit_broken(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            if self.circuit_breaker_reset_time is None:
                self.circuit_breaker_reset_time = time.time() + 60  # 60 second reset
            elif time.time() > self.circuit_breaker_reset_time:
                # Reset circuit breaker
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
            logger.warning(
                f"Circuit breaker opened after {self.circuit_breaker_failures} failures"
            )

    def _generate_insufficient_context_response(self) -> Dict[str, Any]:
        """Generate response when no context is available."""
        response_text = (
            "I don't have enough information in the retrieved sections to answer "
            "this question accurately. Could you try rephrasing or asking about "
            "a topic covered in the book?"
        )

        return {
            "response_text": response_text,
            "generation_params": {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 0,
                "system_prompt_version": "fallback",
                "prompt_token_count": 0,
                "completion_token_count": 0
            },
            "latency_ms": 0
        }

    def _generate_error_response(self) -> Dict[str, Any]:
        """Generate response when generation fails."""
        response_text = (
            "I encountered an error while generating a response. "
            "Please try again in a moment."
        )

        return {
            "response_text": response_text,
            "generation_params": {
                "model": self.model_name,
                "temperature": 0.0,
                "max_tokens": 0,
                "system_prompt_version": "error",
                "prompt_token_count": 0,
                "completion_token_count": 0
            },
            "latency_ms": 0
        }


# Global generation service instance
generation_service = GenerationService()
