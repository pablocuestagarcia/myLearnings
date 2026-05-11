# Modelo Semántico Aplicado a Repositorios de Código

> **Prerrequisitos de lectura:**
> - `01_fundamentos.md` — qué es semántica y qué es un modelo semántico.
> - `02_principios.md` — los dos axiomas que gobiernan este diseño (representar vs. reproducir, y razonamiento bayesiano bajo incertidumbre).
>
> Este documento aplica esos fundamentos al dominio concreto de los repositorios de código.

---

## 1. El Problema: Implementación vs. Intencionalidad

La premisa que vertebra todo este modelo es crítica: **analizar un repositorio basándose únicamente en las herramientas que utiliza es insuficiente**.

- **Enfoque erróneo (Implementación):** "Usa FastAPI, Redis y PostgreSQL". No aporta valor real sobre el propósito del sistema.
- **Enfoque correcto (Intencionalidad):** Describir el *por qué* y el *para qué* existe ("desacoplar el procesamiento asíncrono de la persistencia transaccional para soportar workloads distribuidos").

Esta distinción es el pilar del modelado semántico. Los LLMs y los sistemas de búsqueda basados en *embeddings* puros suelen fallar precisamente aquí: agrupan repositorios por similitud estadística de sus librerías, ignorando si resuelven problemas de negocio completamente opuestos.

La pregunta fundamental que la intencionalidad responde es:

> ¿Por qué existe este sistema?
> ¿Cuál es su propósito fundamental?
> ¿Qué problema de negocio o necesidad humana resuelve?

### Ejemplo concreto

Para un repositorio llamado `distributed-github-fetcher`:

| Tipo | Descripción |
|---|---|
| ❌ Intencionalidad falsa (implementación) | "usar Spark", "hacer llamadas HTTP", "guardar datos en Delta" |
| ✅ Intencionalidad real | "Permitir la extracción escalable y resiliente de datos de GitHub para análisis organizacional" |

---

## 2. La Naturaleza Multidimensional del Software

Para capturar la verdadera esencia de un repositorio, lo modelamos como un **vector multidimensional**. Un repositorio no se puede evaluar en un solo eje, sino que posee diversas facetas que interesan a distintos actores (desarrolladores, arquitectos, negocio, seguridad, *Tech Leads*).

### 2.1. Las 12 dimensiones semánticas

| Dimensión | Qué representa |
|---|---|
| Intención | Problema que resuelve |
| Dominio | Área funcional |
| Capacidades | Funcionalidades |
| Arquitectura | Patrones y diseño |
| Operacional | Comportamiento runtime |
| Infraestructura | Despliegue |
| Dependencias | Ecosistema técnico |
| Datos | Naturaleza de los datos |
| Escalabilidad | Propiedades distribuidas |
| Seguridad | Modelo de trust/auth |
| Observabilidad | Métricas / logging / tracing |
| Organización | Ownership / equipos |

### 2.2. Agrupación analítica de las dimensiones

Para análisis transversal, las 12 dimensiones se pueden agrupar en tres ejes:

- **Eje de Negocio y Producto:** Intención, Dominio, Capacidades, Organización.
- **Eje de Arquitectura y Diseño:** Arquitectura, Datos, Escalabilidad, Seguridad.
- **Eje Técnico y Operacional:** Operacional, Infraestructura, Dependencias, Observabilidad.

**La consecuencia clave de este modelado:** dos repositorios pueden ser **idénticos en su dimensión técnica** (ambos usan *Spark*) pero **diametralmente opuestos en su dimensión de dominio** (uno hace *ETL Financiero* y otro *Análisis de Logs*). Cualquier modelo que no capture esto está mal diseñado.

### 2.3. Materialización: el JSON canónico

```json
{
    "repository": "ghsd-fetcher",
    "intent": ["github_operational_analytics"],
    "domains": ["SCM_ANALYTICS"],
    "capabilities": [
        "github_metadata_extraction",
        "rate_limit_management",
        "distributed_ingestion"
    ],
    "architecture_patterns": [
        "worker_pool",
        "distributed_processing"
    ],
    "storage_models": ["analytical_lakehouse"],
    "operational_characteristics": ["io_bound", "high_concurrency"],
    "technologies": ["spark", "delta_lake", "adls"]
}
```

---

## 3. El Debate Estructural: ¿Cómo almacenamos este conocimiento?

Una vez definidas las dimensiones, surge la pregunta de cómo estructurar estos metadatos a nivel corporativo. Hay dos enfoques en tensión:

### 3.1. El Modelo Canónico (Normalización Estricta)

Consiste en crear una taxonomía centralizada y rígida (un diccionario único de términos permitidos).

- **Ventajas:** Interoperabilidad total. Las consultas cruzadas ("¿cuántas apps tienen la capacidad X?") son triviales.
- **Desventajas:** El ecosistema de software evoluciona más rápido que los diccionarios centrales. Forzar a los equipos a encajar en un esquema rígido provoca fricción y *loss of nuance*.

### 3.2. Ontologías (Grafos de Conocimiento Semántico)

Las ontologías resuelven el problema de la rigidez. En lugar de un JSON plano con propiedades limitadas, usan grafos conceptuales.

- **Relaciones ricas:** No solo atributos, sino direccionalidad y semántica:
  - `ghsd-fetcher` *implements* `Capability:distributed_ingestion`
  - `Capability:distributed_ingestion` *requires* `Technology:spark`
  - `Technology:spark` *is_a* `Concept:Distributed_Compute_Engine`
- **Normalización suave (*soft normalization*):** Resuelve la fricción entre equipos. El equipo A puede usar "extracción" y el B "ingesta"; la ontología define que ambas son subclases de "Adquisición de Datos".
- **Inferencia lógica:** El sistema *deduce* capacidades sin que hayan sido documentadas explícitamente. Si la ontología sabe que *Spark* es un *Distributed Compute Engine*, una búsqueda por "infraestructura distribuida" recuperará `ghsd-fetcher` aunque su JSON nunca tuviera esa etiqueta.

**Conclusión del debate:** el modelo canónico aporta las metas de estandarización; las ontologías evitan que esa estandarización sea frágil. **No son alternativas, son complementarias.**

---

## 4. Representación Computacional: De Textos a Matrices

Para que este modelo semántico sea útil matemáticamente (algoritmos de ML, análisis de grafos, búsqueda vectorial), la información debe traducirse a representaciones matriciales.

### 4.1. Matriz Repositorio-Característica (Entity-Feature)

Matriz dispersa donde las filas son repositorios y las columnas son todas las características posibles del modelo canónico (con valores binarios 1/0 o pesos TF-IDF).

- **Uso típico:** Cálculo de *Similitud del Coseno* y *clustering* no supervisado.
- **Limitación:** Determinista. Solo refleja "lo que el JSON declara explícitamente".

### 4.2. Matriz de Adyacencia (Ontológica)

Representación nativa de los grafos de conocimiento. Tanto repositorios como conceptos operan como nodos.

- **Uso típico:** Operaciones de álgebra lineal para calcular caminos transitivos. Si A se conecta a B y B a C, A infiere C.
- **Aporta:** La **inferencia lógica algorítmica** que el modelo canónico puro no puede ofrecer.

### 4.3. Matriz de Co-ocurrencia

Cruza dimensiones estadísticas empíricas (ej. Tecnología × Intención).

- **Uso típico:** Sistemas de recomendación arquitectónica que aprenden del comportamiento histórico real de la empresa, no de guías estáticas.

### 4.4. La Dimensión Bayesiana: De Matrices Deterministas a Matrices Probabilísticas

> Esta sección conecta directamente con el **Axioma Matemático** de `02_principios.md`.

Las tres matrices anteriores, en su formulación clásica, son **deterministas**: una celda contiene un 1 o un 0, una arista existe o no existe. Esta formulación viola el principio bayesiano de modelado honesto de la incertidumbre. Cuando un LLM infiere que un repositorio "es de pagos", no nos da una verdad — nos da una creencia con una probabilidad asociada.

#### 4.4.1. Reformulación probabilística

Las celdas de la matriz Repositorio-Característica no deben almacenar `{0, 1}`, sino **valores en el intervalo `[0, 1]`** que representen la probabilidad posterior bayesiana de que el repositorio efectivamente posea esa característica:

$$M_{ij} = P(\text{característica}_j \mid \text{evidencia observada en repositorio}_i)$$

Donde el posterior se calcula clásicamente:

$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$

- $P(A)$ = *Prior* corporativo (frecuencia base de la característica en el ecosistema histórico).
- $P(B|A)$ = *Likelihood* (cuán probable es ver esta evidencia técnica si la característica está realmente presente).
- $P(A|B)$ = *Posterior* (la creencia actualizada que efectivamente almacenamos).

#### 4.4.2. Implicaciones prácticas

1. **El JSON canónico se enriquece con confianza.** En lugar de:
   ```json
   "domains": ["payments"]
   ```
   almacenamos:
   ```json
   "domains": { "payments": 0.96, "user_management": 0.04 }
   ```
   Esto es el formato que el axioma matemático exige explícitamente.

2. **Los umbrales de automatización son explícitos.** Reglas como "autocompletar el JSON solo si el *Posterior* supera 0.90; en caso contrario, derivar al *Tech Lead* para revisión manual" se vuelven triviales de implementar.

3. **Aprendizaje orgánico.** Los *Priors* se auto-actualizan. Si la organización vira hacia arquitecturas orientadas a eventos, $P(\text{Event\_Driven})$ crece globalmente, y el sistema tenderá a inferir procesamiento asíncrono con mayor sensibilidad sin reescribir reglas estáticas.

4. **La similitud del coseno se pondera por confianza.** Dos repositorios con `payments: 1.0` y `payments: 0.55` no deberían tratarse como idénticos en esa dimensión.

**Esto es lo que diferencia un catálogo semántico maduro de un simple inventario de etiquetas.**

---

## 5. Automatización: Extracción Semántica mediante LLMs

El mayor obstáculo histórico para mantener modelos semánticos corporativos ha sido el **esfuerzo manual** requerido. El estado del arte actual usa **LLMs como agentes extractores** que pueblan estas matrices automáticamente.

### 5.1. Niveles de fiabilidad por dimensión

| Dimensión extraída | Fuente analizada | Precisión esperada |
|---|---|---|
| **Tecnologías** | Manifiestos (`package.json`, `pom.xml`, `.tf`) | Alta — extracción casi determinista |
| **Capacidades** | Estructura de directorios, *middlewares*, patrones de código | Media-alta — inferencia estructural |
| **Intencionalidad** | `README.md`, docs de arquitectura, jerarquía macro | El mayor reto, ahora resoluble — síntesis semántica del "por qué" |

### 5.2. Mecanismo de salida estructurada

Mediante técnicas de *Structured Output* (function calling, JSON mode, validación contra esquema), el LLM devuelve un `semantic_model.json` validado contra un esquema estricto, listo para insertarse en la matriz corporativa.

### 5.3. Conexión con el modelo bayesiano

Crucialmente, los LLMs modernos pueden devolver **probabilidades calibradas** junto a sus extracciones. Esto los convierte en motores naturales de inferencia bayesiana sobre repositorios: la salida del LLM es directamente el *Posterior* que poblará nuestras matrices probabilísticas (sección 4.4).

---

## 6. El Problema del Vocabulario y el Cálculo de Similitud

Una problemática central al calcular similitudes es la **dispersión léxica**: un equipo escribe `auth-login`, otro `sistema de autenticación`. Para la lógica binaria, son conceptos 100% ajenos. Hay tres formas de mitigarlo.

### 6.1. Enfoque Vectorial Puro (Embeddings)

Convierte todo el texto en vectores numéricos densos en $\mathbb{R}^d$.

- ✅ Maneja sinónimos e idiomas automáticamente por proximidad geométrica.
- ❌ Es una caja negra estadística. Difícil hacer agregaciones deterministas ("¿qué porcentaje exacto de apps tienen la capacidad X?").

### 6.2. Enfoque Canónico (ENUMs Estrictos)

El JSON Schema obliga a elegir valores de una lista maestra inmutable.

- ✅ Similitud matemática perfecta y agregaciones triviales para *dashboards*.
- ❌ Riesgo de obsolescencia rápida y fricción permanente con los equipos.

### 6.3. Enfoque Híbrido Ontológico (Estado del Arte)

La arquitectura más resiliente combina libertad descriptiva con rigor matemático:

1. Se permite el vocabulario local (`auth-login`).
2. La ontología subyacente lo mapea algorítmicamente al concepto normalizado (`Concept:Authentication`).
3. La similitud final se calcula como una **combinación ponderada**:

$$\text{sim}(R_a, R_b) = \alpha \cdot \text{sim}_{\text{ontológica}}(R_a, R_b) + \beta \cdot \text{sim}_{\text{coseno}}(\vec{e}_a, \vec{e}_b)$$

Donde la primera componente captura coincidencia estructural exacta de nodos ontológicos y la segunda captura similitud de *embeddings* de los textos libres descriptivos. Los pesos $\alpha, \beta$ se calibran empíricamente.

Esto otorga **precisión técnica sin perder matices humanos**.

---

## 7. Conclusión: Una Arquitectura Coherente

El modelo completo, una vez integrados los axiomas de `02_principios.md`, traza un recorrido coherente:

1. **Reconoce** que la descripción técnica pura (implementación) es insuficiente para gobernar un ecosistema.
2. **Define** las 12 dimensiones que realmente importan, agrupadas en tres ejes analíticos.
3. **Resuelve** la tensión entre rigidez canónica y flexibilidad mediante el enfoque híbrido ontológico.
4. **Materializa** el conocimiento en matrices computables — no deterministas, sino **probabilísticas y bayesianas**, en coherencia con el axioma matemático del modelo.
5. **Automatiza** la extracción mediante LLMs que producen directamente *Posteriors* calibrados.
6. **Calcula similitud** combinando ontología (rigor estructural) y *embeddings* (matiz semántico).

Esta es la única vía sostenible para gobernar semánticamente el ecosistema de software a escala corporativa, manteniéndose fiel a los dos axiomas: **representar (no reproducir)** y **razonar bajo incertidumbre (no fingir certeza)**.
