# PostgreSQL (Advanced Capabilities Playground)

Este entorno utiliza la imagen `pgvector/pgvector:16` que extiende la imagen oficial de PostgreSQL 16 con la popular extensión de bases de datos vectoriales.

Además de `pgvector`, aprovechamos las características nativas robustas de PostgreSQL.

## Iniciar el entorno

```bash
docker compose up -d
```

## Credenciales de Conexión

- **Host:** `localhost`
- **Puerto:** `5432`
- **Usuario:** `user`
- **Contraseña:** `password`
- **Base de Datos:** `advanced_db`

## Usos Configurados y Ejemplos

El archivo `init-scripts/01-extensions.sql` es ejecutado la primera vez que inicia la base de datos y crea un par de tablas para jugar.

### 1. Colas de Mensajería (Native)

PostgreSQL puede funcionar excelente como sistema de colas usando `FOR UPDATE SKIP LOCKED`. Esta técnica bloquea la fila limitando a que solo un consumidor trabaje con ella en un entorno concurrente.

**Añadir un trabajo a la cola:**
```sql
INSERT INTO job_queue (payload) VALUES ('{"task": "send_email", "to": "user@example.com"}'::jsonb);
```

**Consumir (Worker):**
```sql
UPDATE job_queue
SET status = 'processing', updated_at = NOW()
WHERE job_id = (
    SELECT job_id
    FROM job_queue
    WHERE status = 'pending'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;
```

### 2. Base de Datos Documental con `JSONB`

Gracias al tipo `JSONB`, puedes almacenar y buscar dentro de documentos con alta velocidad, similar a un entorno NoSQL.

```sql
-- Insertar
INSERT INTO documents (content, metadata) 
VALUES ('Este es el contenido principal', '{"author": "Pablo", "tags": ["docker", "postgres"], "views": 100}');

-- Buscar directamente atributos del JSON (aprovecha el índice GIN pre-configurado)
SELECT * FROM documents WHERE metadata @> '{"author": "Pablo"}';

-- Acceder a valores de un array JSON
SELECT * FROM documents WHERE metadata->'tags' ? 'docker';
```

### 3. Base de Datos Vectorial (`pgvector`)

Ideal para sistemas RAG (Retrieval-Augmented Generation) y modelos de IA como embeddings de OpenAI.

```sql
-- Insertar vector (Array de 1536 diemnsiones por lo configurado en la tabla)
INSERT INTO documents (content, embedding) VALUES ('Hola mundo', '[0.1, 0.2, 0.3... 1536 elementos]');

-- Búsqueda de similitud de coseno
SELECT id, content, 1 - (embedding <=> '[0.1, 0.2, 0.3...]') AS similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, 0.3...]'
LIMIT 5;
```

### 4. Búsqueda de Texto Avanzada (FTS y pg_trgm)

Postgres incluye un potente motor Full Text Search y extensiones trigram (`pg_trgm`) para búsqueda parcial o sugerencias "did you mean" (similitud difusa).

```sql
-- Full Text Search simple nativo (tsvector)
SELECT content
FROM documents
WHERE to_tsvector('spanish', content) @@ to_tsquery('spanish', 'contenido');

-- Usando pg_trgm para texto similar/incompleto (aprovecha índice GiST o GIN)
SELECT content
FROM documents
WHERE content ILIKE '%contenid%';
-- ó buscar por similitud:
SELECT content, similarity(content, 'contenydo') AS sim 
FROM documents 
WHERE content % 'contenydo';
```

## Caso de Uso Práctico (Complejidad Media-Baja)

Imagina un sistema donde queremos encontrar registros combinando **filtros avanzados de JSONB** y **Búsqueda de Texto Completo (Full Text Search)** simultáneamente:

```sql
-- 1. Crear tabla de productos
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    attributes JSONB,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('spanish', name || ' ' || description)) STORED
);

-- 2. Insertar productos de prueba
INSERT INTO products (name, description, attributes) VALUES 
('Laptop Pro', 'Portátil de alto rendimiento para desarrolladores.', '{"brand": "TechCorp", "ram": "32GB", "tags": ["laptop", "pro", "dev"]}'),
('Ratón Inalámbrico', 'Ratón ergonómico con batería de larga duración.', '{"brand": "TechCorp", "type": "wireless", "tags": ["mouse", "ergonomic"]}'),
('Monitor 4K', 'Monitor ultrapanorámico especial para programación.', '{"brand": "VisionPlus", "resolution": "4K", "tags": ["monitor", "dev"]}');

-- 3. PRUEBA: Búsqueda combinada
-- Buscar algo relacionado con "programación" o "desarrolladores" que sea de la marca "TechCorp"
SELECT name, description, attributes->>'brand' as marca 
FROM products 
WHERE search_vector @@ to_tsquery('spanish', 'desarrollador | programacion')
  AND attributes @> '{"brand": "TechCorp"}';
```
