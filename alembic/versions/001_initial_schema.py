"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2025-12-12 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Execute initial schema SQL."""
    # Read the SQL file
    sql_file = Path(__file__).parent.parent.parent / "src" / "db" / "migrations" / "001_initial_schema.sql"

    with open(sql_file, 'r') as f:
        sql_statements = f.read()

    # Execute the SQL
    op.execute(sql_statements)


def downgrade() -> None:
    """Drop all tables."""
    op.execute("DROP TABLE IF EXISTS user_feedbacks CASCADE;")
    op.execute("DROP TABLE IF EXISTS query_responses CASCADE;")
    op.execute("DROP TABLE IF EXISTS retrieved_contexts CASCADE;")
    op.execute("DROP TABLE IF EXISTS analytics_aggregates CASCADE;")
    op.execute("DROP TABLE IF EXISTS queries CASCADE;")
    op.execute("DROP TYPE IF EXISTS metric_name_enum;")
    op.execute("DROP EXTENSION IF EXISTS vector;")
