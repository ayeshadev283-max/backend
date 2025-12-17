"""Refusal detector service for anti-hallucination safeguards.

Implements multi-layer refusal detection:
1. Deterministic refusal (before LLM call) based on similarity scores
2. Keyword-based refusal detection (after LLM call)
3. External reference detection (for selected-text mode)
"""
from typing import List, Optional
import re


class RefusalDetector:
    """Detect when queries should be refused or responses contain hallucinations."""

    # Refusal keywords that indicate LLM couldn't answer from context
    REFUSAL_KEYWORDS = [
        "don't have information",
        "does not contain information",
        "not contain sufficient information",
        "cannot answer",
        "outside the scope",
        "not mentioned in",
        "not covered in",
        "insufficient information",
        "unable to find information",
    ]

    # External reference patterns (for selected-text mode)
    EXTERNAL_REFERENCE_PATTERNS = [
        r"Chapter\s+\d+",  # "Chapter 3"
        r"Module\s+\d+",   # "Module 2"
        r"Section\s+\d+",  # "Section 4.2"
        r"see\s+chapter",  # "see chapter X"
        r"as\s+mentioned\s+in\s+chapter",
        r"described\s+in\s+chapter",
    ]

    def should_force_refusal(
        self,
        similarity_scores: List[float],
        threshold: float = 0.7
    ) -> bool:
        """
        Determine if refusal should be forced BEFORE calling LLM.

        This is a cost optimization - if similarity scores are too low,
        refuse immediately without wasting API credits on generation.

        Args:
            similarity_scores: List of similarity scores from retrieval
            threshold: Minimum similarity threshold (default 0.7)

        Returns:
            True if refusal should be forced, False otherwise
        """
        if not similarity_scores:
            # No results found - refuse
            return True

        # Check if maximum similarity is below threshold
        max_similarity = max(similarity_scores)

        return max_similarity < threshold

    def is_refusal_response(self, response_text: str) -> bool:
        """
        Detect if LLM response is a refusal (post-generation check).

        Args:
            response_text: Generated response text from LLM

        Returns:
            True if response contains refusal keywords, False otherwise
        """
        if not response_text:
            return False

        response_lower = response_text.lower()

        # Check for refusal keywords
        for keyword in self.REFUSAL_KEYWORDS:
            if keyword in response_lower:
                return True

        return False

    def detect_external_references(
        self,
        response_text: str,
        allowed_context: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        Detect external chapter/section references in response.

        This is critical for selected-text mode to prevent hallucinations
        where the LLM references content outside the selected text.

        Args:
            response_text: Generated response text
            allowed_context: Optional context description (e.g., "Chapter 1 introduction")

        Returns:
            List of detected external references, or None if none found
        """
        if not response_text:
            return None

        external_refs = []

        for pattern in self.EXTERNAL_REFERENCE_PATTERNS:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                external_refs.append(match.group(0))

        return external_refs if external_refs else None

    def build_refusal_message(
        self,
        query_mode: str,
        reason: str = "low_similarity"
    ) -> str:
        """
        Build appropriate refusal message based on query mode and reason.

        Args:
            query_mode: "book-wide" or "selected-text"
            reason: "low_similarity", "external_reference", or "insufficient_context"

        Returns:
            User-friendly refusal message
        """
        if query_mode == "selected-text":
            # Mandatory refusal message for selected-text mode (per FR-010)
            return "The selected text does not contain sufficient information to answer this question."

        # Book-wide mode refusal messages
        if reason == "low_similarity":
            return "I don't have information about that topic in the book. Please try rephrasing your question or asking about content covered in the chapters."

        if reason == "external_reference":
            return "I cannot answer questions that require information beyond the book's content."

        # Default refusal
        return "I cannot find sufficient information in the book to answer this question."


# Global refusal detector instance
refusal_detector = RefusalDetector()
