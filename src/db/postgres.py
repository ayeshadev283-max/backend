"""Postgres database client wrapper with async connection pooling."""
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import psycopg
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from ..models.config import settings

logger = logging.getLogger(__name__)


class PostgresClientWrapper:
    """Wrapper for Postgres client with async connection pooling."""

    def __init__(self):
        """Initialize Postgres client (pool created on connect)."""
        self.pool: Optional[AsyncConnectionPool] = None

    async def connect(self, min_size: int = 2, max_size: int = 10):
        """
        Create async connection pool to Postgres.

        Args:
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
        """
        try:
            self.pool = AsyncConnectionPool(
                conninfo=settings.database_url,
                min_size=min_size,
                max_size=max_size,
                timeout=30.0
            )
            await self.pool.wait()
            logger.info(f"Connected to Postgres with pool (min={min_size}, max={max_size})")
        except Exception as e:
            logger.error(f"Failed to connect to Postgres: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """
        Get async connection from pool (context manager).

        Usage:
            async with postgres_client.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
        """
        if not self.pool:
            await self.connect()

        async with self.pool.connection() as conn:
            yield conn

    async def execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Any]:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query result or None
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, params)

                    if fetch_one:
                        return await cur.fetchone()
                    elif fetch_all:
                        return await cur.fetchall()
                    else:
                        await conn.commit()
                        return None

                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Query execution failed: {e}")
                    raise

    async def execute_many(self, query: str, params_list: List[tuple]):
        """
        Execute query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.executemany(query, params_list)
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Batch execution failed: {e}")
                    raise

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Closed Postgres connection pool")


# Global Postgres client instance
postgres_client = PostgresClientWrapper()
