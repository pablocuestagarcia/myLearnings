# Capa Semántica Multidimensional para Repositorios

## Problema

Los análisis tradicionales de repositorios suelen centrarse en:

- código,
- dependencias,
- tecnologías,
- embeddings globales.

Esto provoca errores semánticos importantes.

Ejemplo:

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

# Jerarquía Semántica

```text
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

# Ejemplo de Modelo Canónico

```json
{
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
}
```

---

# Modelo Canónico

El objetivo del modelo canónico es:

- normalizar conceptos,
- reducir ambigüedad,
- estabilizar relaciones,
- permitir inferencia consistente.

Ejemplo:

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

# Embeddings Multidimensionales

En lugar de:

```text
repo → embedding único
```

usar:

```text
repo → embeddings especializados
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
(REPO)-[:IMPLEMENTS]->(CAPABILITY)

(REPO)-[:BELONGS_TO]->(DOMAIN)

(REPO)-[:USES_PATTERN]->(ARCH_PATTERN)

(REPO)-[:USES_TECH]->(TECH)

(REPO)-[:SIMILAR_INTENT]->(REPO)
```

---

# Arquitectura Conceptual

```text
Repositorio
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
- dominios,
- capacidades,
- patrones,
- esquema JSON canónico.

---

## Fase 2 — Extracción Estructural

- dependencias,
- lenguajes,
- Docker/K8s,
- CI/CD,
- README,
- metadata GitHub.

---

## Fase 3 — Inferencia Semántica

- prompts LLM,
- clasificación de dominios,
- extracción de capacidades,
- normalización canónica.

---

## Fase 4 — Embeddings

- embeddings especializados,
- clustering,
- similitud multidimensional.

---

## Fase 5 — Grafo Semántico

- Neo4j,
- relaciones,
- reasoning,
- queries semánticas.

---

# Conclusión

El objetivo no es construir únicamente embeddings.

El objetivo es construir:

```text
una representación semántica canónica
y multidimensional del software
```

que permita:

- detectar similitudes reales,
- descubrir reutilización,
- evitar duplicidades,
- realizar reasoning arquitectónico,
- construir inteligencia organizacional sobre repositorios.