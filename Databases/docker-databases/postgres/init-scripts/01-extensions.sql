-- Habilitar extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Habilitar pgvector para almacenamiento de embeddings e indexación vectorial
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar extensión pg_trgm para mejorar la búsqueda de texto parcial y similitudes
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Crear tabla de ejemplo para colas (uso con SKIP LOCKED)
CREATE TABLE IF NOT EXISTS job_queue (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status) WHERE status = 'pending';

-- Crear tabla de ejemplo para documentos JSONB y vectores
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536), -- Asumiendo embeddings de OpenAI por ejemplo (1536 dimensiones)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indice para búsquedas más rápidas en el JSONB
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- Indice para similitud vectorial
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING hnsw (embedding vector_cosine_ops);
