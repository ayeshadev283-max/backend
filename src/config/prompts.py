"""System prompt templates for grounded response generation."""

SYSTEM_PROMPT_TEMPLATE = """You are a helpful educational assistant for students reading "{book_title}".

Your task is to answer student questions ONLY using the provided context from the book.

Rules:
1. Answer ONLY from the context provided below
2. Include source references in your answer (chapter and section)
3. If the context doesn't contain the answer, respond: "I don't have enough information in the retrieved sections to answer this question accurately. Could you try rephrasing or asking about a topic covered in the book?"
4. Do NOT use external knowledge or make assumptions
5. Keep answers concise (2-3 paragraphs maximum)
6. Maintain an encouraging, educational tone

Context:
{retrieved_chunks}

Student Question: {user_query}

Answer:"""


USER_PROMPT_TEMPLATE = """{user_query}"""


def format_system_prompt(
    book_title: str,
    retrieved_chunks: str,
    user_query: str
) -> str:
    """
    Format the system prompt with actual values.

    Args:
        book_title: Title of the book
        retrieved_chunks: Retrieved context from vector database
        user_query: User's question

    Returns:
        Formatted system prompt
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        book_title=book_title,
        retrieved_chunks=retrieved_chunks,
        user_query=user_query
    )


def format_retrieved_chunks(chunks: list) -> str:
    """
    Format retrieved chunks into a readable context string.

    Args:
        chunks: List of chunk dicts with 'payload' containing 'content' and metadata

    Returns:
        Formatted context string
    """
    formatted_chunks = []

    for i, chunk in enumerate(chunks, 1):
        payload = chunk.get('payload', {})
        content = payload.get('content', '')
        chapter = payload.get('chapter_number', '?')
        section = payload.get('section', 'Unknown')

        chunk_text = f"[Source {i} - Chapter {chapter}, {section}]\n{content}\n"
        formatted_chunks.append(chunk_text)

    return "\n".join(formatted_chunks)
