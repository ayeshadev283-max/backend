"""Error handling middleware for FastAPI application."""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from qdrant_client.http.exceptions import UnexpectedResponse as QdrantError
from openai import OpenAIError
from pydantic import ValidationError as PydanticValidationError

from ..models.response import ErrorResponse, ValidationErrorResponse, ValidationError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    validation_errors = []

    for error in exc.errors():
        validation_errors.append(
            ValidationError(
                field=".".join(str(loc) for loc in error.get("loc", [])),
                message=error.get("msg", "Validation error"),
                type=error.get("type", "unknown"),
                value=error.get("input"),
            )
        )

    logger.warning(f"Validation error on {request.url.path}: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ValidationErrorResponse(validation_errors=validation_errors).dict(),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"path": str(request.url.path)},
        ).dict(),
    )


async def qdrant_exception_handler(request: Request, exc: QdrantError):
    """Handle Qdrant client exceptions."""
    logger.error(f"Qdrant error on {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error="Vector search service temporarily unavailable",
            error_code="QDRANT_ERROR",
            details={"message": str(exc)},
        ).dict(),
    )


async def openai_exception_handler(request: Request, exc: OpenAIError):
    """Handle OpenAI API exceptions."""
    logger.error(f"OpenAI error on {request.url.path}: {exc}", exc_info=True)

    # Check for specific error types
    error_message = "AI generation service temporarily unavailable"
    error_code = "OPENAI_ERROR"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    if "rate limit" in str(exc).lower():
        error_message = "Rate limit exceeded, please try again later"
        error_code = "RATE_LIMIT_ERROR"
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif "authentication" in str(exc).lower() or "api key" in str(exc).lower():
        error_message = "AI service configuration error"
        error_code = "AUTHENTICATION_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error_message,
            error_code=error_code,
            details={"message": str(exc)},
        ).dict(),
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(QdrantError, qdrant_exception_handler)
    app.add_exception_handler(OpenAIError, openai_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
