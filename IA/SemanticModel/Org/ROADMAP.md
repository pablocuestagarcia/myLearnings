# Roadmap: Semantic Modeling Ecosystem

Este documento traza la hoja de ruta de la investigación y desarrollo en torno a la extracción, representación y gobierno del conocimiento arquitectónico mediante Inteligencia Artificial (Modelos Semánticos).

## ✅ FASE 1: Investigación y Fundamentación Teórica
El objetivo de esta fase ha sido asentar las bases teóricas para evitar los errores comunes de los sistemas de catálogos tradicionales (*Developer Portals*).

- [x] **Distinción Fundamental:** Teorización sobre Intencionalidad vs. Implementación (`research_about_semantic.md`).
- [x] **Dimensionalidad:** Definición de los ejes de análisis de un repositorio (Negocio, Arquitectura, Operaciones).
- [x] **Estructuras de Almacenamiento:** Análisis comparativo entre el Modelo Canónico (JSON estricto) y Ontologías / Grafos de conocimiento (`semantic_research_analysis.md`).
- [x] **Principios Filosóficos:** Establecimiento de la dicotomía "Reproducir vs. Representar" y aplicación del razonamiento Bayesiano bajo incertidumbre (`semantic_model_philosophy.md`).
- [x] **Arquitectura de Extracción:** Diseño teórico del Pipeline Agéntico para reducción de costes y agnosia de lenguajes (`pipeline_agente_extractor.md`).

## 🔄 FASE 2: Definición Estructural (En progreso)
Traducción de los principios filosóficos a esquemas computacionales concretos.

- [ ] **Diseño del JSON Schema (v1):** Creación del esquema canónico oficial que deberán escupir los agentes (`semantic_model_v1.json`).
- [ ] **Glosario Canónico Base:** Definir una lista inicial de `domains`, `intentions` y `capabilities` genéricas como semilla para la ontología.

## 📅 FASE 3: Pruebas de Concepto (PoC)
Implementación técnica de las ideas desarrolladas en la teoría.

- [ ] **PoC Agente Extractor:** Desarrollar un script en Python (usando LangChain/CrewAI o llamadas directas a la API de LLMs con *Structured Output* y *Tools*) que ejecute las fases de reconocimiento en repositorios locales.
- [ ] **Evaluación de Costes reales:** Medir el consumo real de tokens procesando 5 repositorios de distintos lenguajes (ej. R, C++, TypeScript).
- [ ] **PoC Matriz Bayesiana:** Crear un script básico que calcule probabilidades condicionales a partir de un puñado de archivos JSON inferidos.

## 📅 FASE 4: Casos de Uso (Integración)
Demostrar el valor empresarial del modelo semántico extraído.

- [ ] **Búsqueda Semántica:** Demostrar cómo encontrar repositorios por su Intención usando *Embeddings* combinados con el Modelo Canónico.
- [ ] **Recomendación Arquitectónica:** Prototipar un recomendador que aconseje herramientas basado en la Matriz de Co-ocurrencia.
