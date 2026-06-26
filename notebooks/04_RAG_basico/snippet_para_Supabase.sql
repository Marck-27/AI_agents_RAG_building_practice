-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- 1. Crear la tabla para almacenar tus documentos
-- Esta tabla usa los nombres de tu script de Python.
create table if not exists documentos_vectorizados (
  id uuid primary key,
  content text,
  metadata jsonb,
  -- El embedding es de 1536 dimensiones porque usas el modelo 'text-embedding-ada-002' de OpenAI
  embedding vector (1536) 
);

-- 2. Crear la función para buscar documentos por similitud
-- Esta función también usa el nombre personalizado de tu script.
create or replace function similar_documentos_vectorizados (
  query_embedding vector(1536),
  match_count int,
  filter jsonb
) returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    id,
    content,
    metadata,
    1 - (documentos_vectorizados.embedding <=> query_embedding) as similarity
  from documentos_vectorizados
  where metadata @> filter
  order by documentos_vectorizados.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- 3. Establecer un valor predeterminado para la columna 'id' usando la función gen_random_uuid()
alter table documentos_vectorizados
alter column id set default gen_random_uuid();