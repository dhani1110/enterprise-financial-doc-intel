-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Example table for storing documents with embeddings (optional)
-- Adjust dimension to match your embedding provider (e.g., OpenAI/text-embedding-ada-002: 1536)
--
-- CREATE TABLE documents (
--   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--   content text,
--   metadata jsonb,
--   embedding vector(1536)
-- );
