# Intencionalidad

En ingeniería de software, arquitectura y modelado semántico, términos como intencionalidad, objetivos, capacidades o mecanismos representan distintos niveles de abstracción para describir un sistema.

La intencionalidad responde a:
> ¿Por qué existe este sistema?
> ¿Cuál es su propósito fundamental?
> ¿Qué problema de negocio o necesidad humana resuelve?

Es la motivación fundamental del sistema.
No habla de implementación, ni tecnologías, ni algoritmos, solo del para qué existe.

## Ejemplo

Imagina un repositorio llamado:

distributed-github-fetcher

La intencionalidad NO es:

❌ “usar Spark”
❌ “hacer llamadas HTTP”
❌ “guardar datos en Delta”

La intencionalidad sería algo como:

✅ “Permitir la extracción escalable y resiliente de datos de GitHub para análisis organizacional.”

# Objetivos

# Capacidades

# Mecanismos

# Herramientas o tecnologías

# Diferencia entre intención e implementación

Muchos análisis de repositorios fallan porque describen únicamente implementación.

Ejemplo malo:

> “El sistema usa FastAPI, Redis y PostgreSQL.”

Eso no explica nada importante.

En cambio:

> “El sistema busca desacoplar procesamiento asíncrono de persistencia transaccional para soportar workloads distribuidos.”

Eso sí describe significado arquitectónico.

Cuando hablas de construir un “modelo semántico” de un repositorio, realmente intentas capturar:

intención
dominio
capacidades
restricciones
decisiones arquitectónicas
trade-offs
comportamiento emergente

No solo texto o código.

Por eso un embedding puro suele ser insuficiente:
captura proximidad estadística,
pero no necesariamente intención estructurada.

# Un repositorio

Un repositorio es por tanto, una representación semántica multidimensional. Dos repositorios pueden ser cercanos en un espacio y lejanos en otro. Y eso es perfectamente válido.

| Espacio         | Qué representa           |
| --------------- | ------------------------ |
| Intención       | problema que resuelve    |
| Dominio         | área funcional           |
| Capacidades     | funcionalidades          |
| Arquitectura    | patrones y diseño        |
| Operacional     | comportamiento runtime   |
| Infraestructura | despliegue               |
| Dependencias    | ecosistema técnico       |
| Datos           | naturaleza de los datos  |
| Escalabilidad   | propiedades distribuidas |
| Seguridad       | modelo de trust/auth     |
| Observabilidad  | métricas/logging/tracing |
| Organización    | ownership/equipos        |

```json
{
    "repository": "ghsd-fetcher",
    "intent": [
        "github_operational_analytics"
    ],
    "domains": [
        "SCM_ANALYTICS"
    ],
    "capabilities": [
        "github_metadata_extraction",
        "rate_limit_management",
        "distributed_ingestion"
    ],
    "architecture_patterns": [
        "worker_pool",
        "distributed_processing"
    ],
    "storage_models": [
        "analytical_lakehouse"
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

# Modelo Canónico (o Normalizado)

A la hora de estructurar esta "representación semántica multidimensional" (como el JSON del ejemplo anterior), surge la necesidad de un **Modelo Canónico** (Canonical Model).

En arquitectura empresarial y de software, un modelo canónico es un patrón de diseño que establece un lenguaje común o "lingua franca". En el contexto de un ecosistema de repositorios, esto significaría definir una taxonomía estandarizada para nuestros vectores de metadatos:
- ¿Existe un catálogo central de "Intenciones" válidas?
- ¿Están todas las "Capacidades" tipificadas (ej. `rate_limit_management` vs `handle_api_limits`)?

**Ventajas de la normalización:**
- **Interoperabilidad y Búsqueda:** Facilita enormemente las consultas globales, agregaciones y comparaciones directas. Si todos usan el mismo identificador para una capacidad, el cruce de datos es trivial.
- **Gobernanza:** Evita la dispersión y la ambigüedad en la terminología (el clásico problema de *data silos* semánticos).

**Desafíos:**
- **Rigidez vs Evolución:** El software es un entorno altamente dinámico. Imponer un modelo canónico estricto, centralizado y jerárquico puede convertirse en un cuello de botella.
- **Pérdida de matiz:** Al forzar descripciones a encajar en "cajas predefinidas", podemos perder el contexto específico y la verdadera intencionalidad original del equipo.

# Ontologías: Más allá de esquemas rígidos

Aquí es donde las **Ontologías** ofrecen un enfoque superior frente a los esquemas relacionales o documentos JSON estáticos (modelos canónicos puros). 

Mientras que un modelo normalizado suele ser un esquema restrictivo ("estas son las propiedades permitidas"), una ontología es una representación formal y explícita del conocimiento basada en conceptos y relaciones (grafos).

¿Cómo nos ayudan las ontologías en la representación semántica de repositorios?

1. **Relaciones Ricas (Grafos de Conocimiento):**
   No solo definimos listas de *strings*, sino grafos con semántica direccional.
   - `ghsd-fetcher` → *implements* → `Capability: distributed_ingestion`
   - `Capability: distributed_ingestion` → *requires* → `Technology: spark`
   - `Technology: spark` → *is_a* → `Concept: Distributed_Compute_Engine`

2. **Inferencia y Razonamiento Lógico:**
   Esta es la gran ventaja ontológica. Si nuestro modelo ontológico sabe que *Spark* es un tipo de *Distributed Compute Engine*, cuando busquemos "repositorios que requieren infraestructura distribuida", `ghsd-fetcher` aparecerá automáticamente, aunque su JSON original nunca tuviera la etiqueta explícita `distributed_infrastructure`. La ontología **deduce** las capacidades y dependencias implícitas a partir de las herramientas y las reglas definidas.

3. **Flexibilidad y Normalización "Suave" (Soft Normalization):**
   Las ontologías permiten mapear vocabularios locales a conceptos globales. Un equipo puede describir su repositorio usando sus propios términos (ej. "data_extraction"), y la ontología puede definir que `data_extraction` y `data_ingestion` son conceptos equivalentes o subclases de un nodo superior `DataAcquisition`.
   Esto nos da lo mejor de ambos mundos: libertad descriptiva para los desarrolladores y capacidad de análisis global estandarizado para la organización.

**En resumen**, para modelar un ecosistema de software a nivel semántico:
- El **Modelo Canónico** nos da las metas de estandarización necesarias para que los datos sean comparables y estructurados.
- Las **Ontologías** evitan que esa estandarización sea un esquema rígido y frágil, aportando capacidad de inferencia algorítmica, relaciones dinámicas y un mecanismo flexible para conectar el vocabulario humano (intencionalidad) con la representación computacional (implementación).