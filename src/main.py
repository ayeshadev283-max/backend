"""FastAPI application entry point."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from .models.config import settings
from .config.logging import setup_logging
from .db.postgres import postgres_client
from .db.qdrant import qdrant_client

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RAG Chatbot API...")

    if settings.dev_mode:
        logger.warning("⚠️  Running in DEV_MODE - database connections disabled")
        logger.warning("⚠️  API endpoints requiring database will not work")
    else:
        try:
            # Connect to Postgres
            await postgres_client.connect()
            logger.info("Connected to Postgres")

            # Connect to Qdrant
            qdrant_client.connect()
            logger.info("Connected to Qdrant")

            # Ensure Qdrant collection exists (768 for Google text-embedding-004)
            qdrant_client.ensure_collection(vector_size=768)
            logger.info("Qdrant collection ready")

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot API...")
    if not settings.dev_mode:
        await postgres_client.close()
        qdrant_client.close()
    logger.info("Connections closed")


# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API for Educational Resources",
    description="REST API for the Retrieval-Augmented Generation (RAG) chatbot system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Docusaurus dev server
        "http://127.0.0.1:3000",
        "https://*.github.io",  # GitHub Pages
        "https://*.vercel.app",  # Vercel deployments
        "https://*.hf.space",  # Hugging Face Spaces
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid request",
            "message": "Request validation failed",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


# Health endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Check API health status.

    Returns system health information including service availability.
    """
    from datetime import datetime

    # Check database connections
    db_status = "healthy"
    vector_db_status = "healthy"
    openai_status = "healthy"  # Placeholder - would need actual check

    try:
        # Test Postgres connection
        await postgres_client.execute("SELECT 1", fetch_one=True)
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        db_status = "unhealthy"

    try:
        # Test Qdrant connection
        if not qdrant_client.client:
            qdrant_client.connect()
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        vector_db_status = "unhealthy"

    # Determine overall status
    overall_status = "healthy"
    if db_status == "unhealthy" or vector_db_status == "unhealthy":
        overall_status = "degraded"
    if db_status == "unhealthy" and vector_db_status == "unhealthy":
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "database": db_status,
            "vector_db": vector_db_status,
            "openai_api": openai_status
        },
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Chatbot API",
        "version": "1.0.0",
        "description": "Retrieval-Augmented Generation chatbot for educational resources",
        "docs_url": "/docs",
        "health_url": "/health"
    }


# API routers
from .api import query  # , analytics  # TODO: Fix analytics - missing SQLAlchemy dependency

app.include_router(query.router, prefix="/v1", tags=["query"])

# Additional routers will be added as they are implemented
# from .api import feedback
# app.include_router(feedback.router, prefix="/v1", tags=["feedback"])
# app.include_router(analytics.router)  # TODO: Re-enable once analytics is fixed
