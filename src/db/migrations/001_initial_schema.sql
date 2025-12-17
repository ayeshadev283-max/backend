-- Initial database schema for RAG Chatbot
-- Based on data-model.md specifications

-- Enable pgvector extension for vector similarity
CREATE EXTENSION IF NOT EXISTS vector;

-- Queries table
CREATE TABLE IF NOT EXISTS queries (
  query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id VARCHAR(64) NOT NULL,
  query_text TEXT NOT NULL CHECK (length(query_text) BETWEEN 1 AND 500),
  query_embedding vector(1536) NOT NULL,
  selected_text TEXT,
  book_context JSONB,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  session_id UUID,
  ip_address_hash VARCHAR(64),
  CONSTRAINT valid_user_id CHECK (length(user_id) = 64)
);

CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id);
CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_queries_book_context ON queries((book_context->>'book_id'), timestamp DESC);

-- Retrieved Contexts table
CREATE TABLE IF NOT EXISTS retrieved_contexts (
  context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL REFERENCES queries(query_id) ON DELETE CASCADE,
  chunk_ids UUID[] NOT NULL CHECK (array_length(chunk_ids, 1) BETWEEN 1 AND 10),
  similarity_scores FLOAT[] NOT NULL,
  retrieval_params JSONB NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT matching_array_lengths CHECK (array_length(chunk_ids, 1) = array_length(similarity_scores, 1))
);

CREATE INDEX IF NOT EXISTS idx_retrieved_contexts_query_id ON retrieved_contexts(query_id);
CREATE INDEX IF NOT EXISTS idx_retrieved_contexts_timestamp ON retrieved_contexts(timestamp DESC);

-- Query Responses table
CREATE TABLE IF NOT EXISTS query_responses (
  response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL UNIQUE REFERENCES queries(query_id) ON DELETE CASCADE,
  response_text TEXT NOT NULL CHECK (length(response_text) BETWEEN 50 AND 2000),
  source_references JSONB NOT NULL,
  generation_params JSONB NOT NULL,
  latency_ms INTEGER NOT NULL CHECK (latency_ms BETWEEN 100 AND 10000),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  confidence_score FLOAT CHECK (confidence_score BETWEEN 0.0 AND 1.0)
);

CREATE INDEX IF NOT EXISTS idx_query_responses_query_id ON query_responses(query_id);
CREATE INDEX IF NOT EXISTS idx_query_responses_timestamp ON query_responses(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_query_responses_confidence ON query_responses(confidence_score);

-- User Feedbacks table
CREATE TABLE IF NOT EXISTS user_feedbacks (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  response_id UUID NOT NULL UNIQUE REFERENCES query_responses(response_id) ON DELETE CASCADE,
  rating VARCHAR(20) NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
  comment TEXT CHECK (length(comment) <= 500),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_feedbacks_response_id ON user_feedbacks(response_id);
CREATE INDEX IF NOT EXISTS idx_user_feedbacks_rating ON user_feedbacks(rating);
CREATE INDEX IF NOT EXISTS idx_user_feedbacks_timestamp ON user_feedbacks(timestamp DESC);

-- Analytics Aggregates table
DO $$ BEGIN
    CREATE TYPE metric_name_enum AS ENUM (
        'daily_query_count',
        'weekly_avg_latency',
        'monthly_feedback_rate',
        'top_question_topics',
        'hourly_concurrent_users'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS analytics_aggregates (
  aggregate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_name metric_name_enum NOT NULL,
  time_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
  time_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
  metric_value JSONB NOT NULL,
  book_id VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT valid_time_period CHECK (time_period_end > time_period_start)
);

CREATE INDEX IF NOT EXISTS idx_analytics_aggregates_lookup ON analytics_aggregates(metric_name, time_period_start, book_id);
CREATE INDEX IF NOT EXISTS idx_analytics_aggregates_time ON analytics_aggregates(time_period_start DESC);
