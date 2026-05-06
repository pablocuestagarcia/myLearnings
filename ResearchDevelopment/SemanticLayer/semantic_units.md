# Capa Semántica Multidimensional para Repositorios

# Problema

Los análisis tradicionales de repositorios suelen centrarse en:

- código,
- dependencias,
- tecnologías,
- embeddings globales.

Esto provoca errores semánticos importantes.

## Ejemplo

| Repo | Descripción |
|---|---|
| A | Extrae datos de GitHub con Go y PostgreSQL |
| B | Extrae datos de GitHub con Spark y ADLS |
| C | Extrae datos de Jira con Python y PostgreSQL |

Semánticamente:

```text
A ≈ B
```

porque comparten intención funcional.

Pero tecnológicamente:

```text
A ≈ C
```

porque comparten stack similar.

Esto demuestra que:

```text
la similitud entre repositorios no es única
```

---

# Hipótesis

Un repositorio debe representarse como:

```text
una entidad semántica multidimensional
```

donde cada dimensión representa un espacio semántico distinto.

---

# Espacios Semánticos

| Espacio | Representa |
|---|---|
| Intención | Qué problema resuelve |
| Dominio | Área funcional |
| Capacidades | Qué sabe hacer |
| Arquitectura | Cómo organiza el sistema |
| Operacional | Comportamiento runtime |
| Infraestructura | Modelo de despliegue |
| Persistencia | Estrategia de almacenamiento |
| Dependencias | Ecosistema técnico |

---

# Problema de los Monorepos

La hipótesis inicial:

```text
1 repositorio = 1 sistema semántico
```

es incorrecta para:

- monorepos,
- plataformas internas,
- microservicios,
- data platforms,
- repositorios multi-dominio.

## Ejemplo

```text
monorepo/
├── github-ingestion/
├── analytics-engine/
└── dashboard-api/
```

Cada módulo puede representar:

- intenciones distintas,
- capacidades distintas,
- arquitecturas distintas,
- relaciones distintas.

Por tanto:

```text
1 repositorio ≠ 1 entidad semántica
```

---

# Semantic Units

La verdadera entidad semántica pasa a ser:

```text
semantic unit
```

Una semantic unit representa una unidad funcional coherente.

## Ejemplos

- microservicio,
- pipeline,
- librería,
- bounded context,
- motor analítico,
- API,
- worker,
- componente ML.

---

# Nuevo Modelo Conceptual

```text
Repository
    └── Semantic Units
            └── Semantic Layers
```

---

# Jerarquía Completa

```text
REPOSITORY
    ↓
SEMANTIC UNIT
    ↓
INTENCIÓN
    ↓
DOMINIO
    ↓
CAPACIDADES
    ↓
MECANISMOS
    ↓
PATRONES
    ↓
TECNOLOGÍAS
```

---

# Ejemplo de Monorepo

```text
platform-monorepo/
├── github-ingestion/
├── analytics-engine/
└── ml-scoring/
```

---

# Semantic Unit: github-ingestion

## Intent

```text
github_operational_analytics
```

## Capabilities

- github_metadata_extraction
- rate_limit_management
- distributed_ingestion

## Technologies

- Spark
- Delta Lake
- ADLS

---

# Semantic Unit: analytics-engine

## Intent

```text
repository_behavior_analysis
```

## Capabilities

- repository_analysis
- trend_detection
- aggregation

## Technologies

- Python
- PostgreSQL

---

# Relaciones Internas

```text
analytics-engine
    DEPENDS_ON
github-ingestion
```

---

# Modelo Canónico

El objetivo del modelo canónico es:

- normalizar conceptos,
- reducir ambigüedad,
- estabilizar relaciones,
- permitir inferencia consistente.

## Ejemplo

```text
GitHub ingestion
SCM harvester
Repo sync engine
```

↓

```text
github_metadata_extraction
```

---

# Ejemplo de Modelo Canónico

```json
{
  "repository": "platform-monorepo",

  "semantic_units": [
    {
      "name": "github-ingestion",

      "intent": [
        "github_operational_analytics"
      ],

      "domains": [
        "SCM_ANALYTICS"
      ],

      "capabilities": [
        "github_metadata_extraction",
        "distributed_ingestion"
      ],

      "architecture_patterns": [
        "worker_pool"
      ],

      "operational_characteristics": [
        "io_bound",
        "high_concurrency"
      ],

      "technologies": [
        "spark",
        "delta_lake",
        "adls"
      ]
    },

    {
      "name": "analytics-engine",

      "intent": [
        "repository_behavior_analysis"
      ],

      "domains": [
        "SCM_ANALYTICS"
      ],

      "capabilities": [
        "repository_analysis",
        "aggregation"
      ],

      "technologies": [
        "python",
        "postgresql"
      ]
    }
  ]
}
```

---

# Embeddings Multidimensionales

En lugar de:

```text
repo → embedding único
```

usar:

```text
semantic unit → embeddings especializados
```

## Ejemplos

| Embedding | Representa |
|---|---|
| Intent embedding | propósito |
| Capability embedding | funcionalidades |
| Architecture embedding | patrones |
| Tech embedding | stack |

---

# Knowledge Graph

El objetivo final es construir un grafo semántico software.

## Relaciones

```text
(REPOSITORY)-[:CONTAINS]->(SEMANTIC_UNIT)

(SEMANTIC_UNIT)-[:IMPLEMENTS]->(CAPABILITY)

(SEMANTIC_UNIT)-[:BELONGS_TO]->(DOMAIN)

(SEMANTIC_UNIT)-[:USES_PATTERN]->(ARCH_PATTERN)

(SEMANTIC_UNIT)-[:USES_TECH]->(TECH)

(SEMANTIC_UNIT)-[:DEPENDS_ON]->(SEMANTIC_UNIT)

(SEMANTIC_UNIT)-[:SIMILAR_TO]->(SEMANTIC_UNIT)
```

---

# Arquitectura Conceptual

```text
Repositorio
    ↓
Detección de semantic units
    ↓
Extracción estructural
    ↓
Inferencia semántica
    ↓
Modelo canónico
    ↓
Embeddings multidimensionales
    ↓
Knowledge Graph
```

---

# Roadmap

## Fase 1 — Modelo Semántico

- definir taxonomía,
- definir semantic units,
- definir dominios,
- definir capacidades,
- definir patrones,
- diseñar esquema JSON canónico.

---

## Fase 2 — Detección de Semantic Units

- análisis estructura carpetas,
- build systems,
- package managers,
- Dockerfiles,
- CI/CD,
- ownership,
- imports y dependencias internas.

---

## Fase 3 — Extracción Estructural

- dependencias,
- lenguajes,
- infraestructura,
- observabilidad,
- pipelines,
- metadata GitHub.

---

## Fase 4 — Inferencia Semántica

- prompts LLM,
- clasificación dominios,
- extracción capacidades,
- detección patrones,
- normalización canónica.

---

## Fase 5 — Embeddings

- embeddings especializados,
- similitud multidimensional,
- clustering por espacio semántico.

---

## Fase 6 — Knowledge Graph

- Neo4j,
- relaciones semánticas,
- reasoning,
- queries arquitectónicas.

---

# Conclusión

El repositorio ya no debe considerarse la unidad semántica principal.

El repositorio es:

```text
un contenedor físico
```

La verdadera entidad semántica es:

```text
la semantic unit
```

sobre la que se construyen:

- embeddings,
- relaciones,
- capacidades,
- similitudes,
- reasoning arquitectónico,
- knowledge graphs semánticos.