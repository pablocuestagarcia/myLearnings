# Docker Databases Playground

Este espacio está diseñado para probar, configurar y aprender sobre diferentes bases de datos ejecutándose en local mediante Docker.

Cada subdirectorio contiene un entorno específico y auto-contenido con su propio `docker-compose.yml` y una guía sobre cómo usarlo y configurarlo adecuadamente.

## Bases de Datos Disponibles

- [**PostgreSQL (`/postgres`)**](./postgres): Configurado para escenarios avanzados. Incluye:
  - Vector embeddings con la extensión `pgvector`.
  - Uso de tipos `JSONB` para almacenamiento similar a bases de datos orientadas a documentos.
  - Búsqueda de texto avanzada (Full Text Search) combinada con índices GiST/GIN.
  - Colas y mensajería nativa utilizando `FOR UPDATE SKIP LOCKED`.
- [**Neo4j (`/neo4j`)**](./neo4j): Base de datos nativa de grafos, ideal para almacenar y consultar datos altamente interconectados utilizando el lenguaje Cypher.
- [**SurrealDB (`/surrealdb`)**](./surrealdb): Base de datos multi-modelo que combina características de documentos, grafos, relacional y real-time en una sola plataforma con su propio lenguaje SurrealQL.

## Requisitos Previos

- Docker y Docker Compose instalados en tu sistema local.

## Instrucciones Generales

1. Entra en el directorio de la base de datos que quieras probar: `cd postgres`
2. Levanta el contenedor: `docker compose up -d`
3. Consulta el `README.md` dentro de esa carpeta para interactuar con la base de datos.
4. Para detener y limpiar el entorno cuando termines: `docker compose down -v` (el `-v` elimina los volúmenes, eliminando los datos paraempezar desde cero la próxima vez).
