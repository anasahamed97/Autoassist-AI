-- ==============================================================================
-- AutoAssist AI: Supabase PostgreSQL + pgvector Database Schema
-- Milestone 1: Automotive Knowledge Base & Vector Retrieval
-- ==============================================================================

-- 1. Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the 'documents' table to store automotive technical literature metadata
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    manufacturer TEXT,
    vehicle_model TEXT,
    model_year INTEGER,
    document_type TEXT, -- e.g., 'Service Manual', 'Troubleshooting Guide', 'Owner Manual'
    source TEXT,
    source_url TEXT,
    content_hash TEXT UNIQUE, -- SHA-256 hash to ensure idempotent ingestion without duplicate records
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Create the 'document_chunks' table with 384-dimensional vector embeddings
-- 384 matches the standard sentence-transformers/all-MiniLM-L6-v2 embedding model
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    chunk_index INTEGER NOT NULL,
    section TEXT,
    page_number INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Create an HNSW index on the vector embeddings for fast approximate nearest neighbor (ANN) search
-- HNSW provides sub-millisecond retrieval latency for cosine distance
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON public.document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Auxiliary indexes for fast relational lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_manufacturer ON public.documents(manufacturer);
CREATE INDEX IF NOT EXISTS idx_documents_vehicle_model ON public.documents(vehicle_model);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON public.documents(content_hash);

-- 5. Stored Procedure (RPC) for Semantic Similarity Search
-- Computes cosine similarity (1 - cosine distance) and joins parent document metadata
CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding vector(384),
    match_threshold double precision DEFAULT 0.20,
    match_count integer DEFAULT 5,
    filter_metadata jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    similarity double precision,
    document_title TEXT,
    manufacturer TEXT,
    vehicle_model TEXT,
    model_year INTEGER,
    document_type TEXT,
    section TEXT,
    page_number INTEGER,
    source TEXT,
    source_url TEXT,
    metadata JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        ROUND((1 - (dc.embedding <=> query_embedding))::numeric, 4)::double precision AS similarity,
        d.title AS document_title,
        d.manufacturer,
        d.vehicle_model,
        d.model_year,
        d.document_type,
        dc.section,
        dc.page_number,
        d.source,
        d.source_url,
        dc.metadata
    FROM public.document_chunks dc
    JOIN public.documents d ON dc.document_id = d.id
    WHERE 
        (1 - (dc.embedding <=> query_embedding)) >= match_threshold
        -- Optional JSONB metadata filtering if provided
        AND (filter_metadata = '{}'::jsonb OR dc.metadata @> filter_metadata)
    ORDER BY dc.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;

-- 6. Row Level Security (RLS) Configuration
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

-- Allow public read access to documents and chunks (for retrieval)
CREATE POLICY "Allow public read access to documents"
ON public.documents FOR SELECT
TO anon, authenticated
USING (true);

CREATE POLICY "Allow public read access to document chunks"
ON public.document_chunks FOR SELECT
TO anon, authenticated
USING (true);

-- Allow service role full write access (for ingestion pipelines)
CREATE POLICY "Allow service_role full access to documents"
ON public.documents FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Allow service_role full access to document chunks"
ON public.document_chunks FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
