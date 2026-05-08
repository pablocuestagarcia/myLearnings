# Plan de Estudio: Probabilistic Graphical Models (PGMs)

Este plan está diseñado para abordar la especialización de PGMs construyendo primero una base sólida en matemáticas y programación, para luego avanzar por los tres cursos de forma estructurada.

## Fase 0: Preparación y Fundamentos (1-2 Semanas)
Antes de empezar el Curso 1, asegúrate de dominar estos conceptos. Si intentas aprenderlos sobre la marcha, la carga cognitiva será demasiado alta.

### Matemáticas y Probabilidad
*   **Probabilidad:** Repasa la regla de Bayes, probabilidad marginal, probabilidad condicional, y el concepto de "Independencia Condicional" (vital para PGMs).
*   **Álgebra Lineal:** Operaciones con matrices y vectores.
*   **Recursos recomendados:** 
    *   *Khan Academy* (Probabilidad y Estadística).
    *   *Mathematics for Machine Learning* (Libro o curso corto).

### Teoría de Grafos
*   Conceptos básicos: Nodos, aristas dirigidas/no dirigidas, caminos, ciclos, Grafos Acíclicos Dirigidos (DAGs), cliques.

### Programación (Python)
*   Asegúrate de tener soltura con `numpy` (para operaciones matriciales) y `scipy`.
*   Familiarízate con la librería `pgmpy` (Probabilistic Graphical Models in Python). Es la herramienta estándar en Python para implementar lo que aprenderás teóricamente.

---

## Fase 1: Curso 1 - Representation (3-4 Semanas)
El objetivo aquí es entender cómo traducir un problema del mundo real (semántica causal) a un grafo matemático.

### Foco de Estudio:
1.  **Redes Bayesianas (Grafos Dirigidos):** Entiende cómo las flechas codifican causalidad y cómo se definen las Tablas de Probabilidad Condicional (CPDs).
2.  **Redes de Markov (Grafos No Dirigidos):** Aprende cuándo usarlas (cuando hay correlación pero no causalidad clara) y qué son los "factores" y la función de partición.
3.  **Independencia:** Domina el concepto de *d-separación* (en grafos dirigidos) y *separación activa* (en grafos no dirigidos). Es la pregunta de examen más común.

### Acción Práctica:
*   Intenta modelar un problema cotidiano (ej. diagnóstico de por qué el coche no arranca o un diagnóstico médico simple) dibujando el grafo y definiendo sus CPDs.
*   Codifica ese modelo usando `pgmpy`.

---

## Fase 2: Curso 2 - Inference (4 Semanas)
Este es probablemente el curso más duro matemáticamente. Trata sobre cómo usar el grafo creado en la Fase 1 para responder preguntas (ej. dada una evidencia, ¿cuál es la probabilidad de un evento oculto?).

### Foco de Estudio:
1.  **Inferencia Exacta:** Variable Elimination y el algoritmo de Message Passing / Belief Propagation en árboles (Junction Trees).
2.  **Inferencia Aproximada:** Entiende por qué la inferencia exacta es NP-Hard en grafos complejos. Estudia los métodos basados en Muestreo (MCMC - Markov Chain Monte Carlo, Gibbs Sampling).
3.  **MAP (Maximum a Posteriori):** Cómo encontrar la configuración más probable de las variables.

### Acción Práctica:
*   Programa el algoritmo de *Variable Elimination* desde cero para un grafo pequeño de 3-4 nodos. Esto consolidará tu entendimiento de cómo se multiplican y marginalizan los "factores".

---

## Fase 3: Curso 3 - Learning (4 Semanas)
Aquí se une todo con el Machine Learning clásico. Tienes datos y quieres que el modelo aprenda el grafo por sí solo.

### Foco de Estudio:
1.  **Estimación de Parámetros:** Si ya conoces la estructura del grafo, ¿cómo estimas las probabilidades a partir de los datos? (Maximum Likelihood Estimation - MLE y enfoques Bayesianos).
2.  **Aprendizaje de Estructura:** Si no conoces el grafo, ¿cómo lo deduces de los datos? Estudia métodos basados en puntuación (Score-based) y basados en restricciones (Constraint-based).
3.  **Datos Incompletos:** El poderoso algoritmo **Expectation-Maximization (EM)** para aprender cuando hay variables ocultas.

### Acción Práctica:
*   Usa un dataset público tabular (como el dataset del Titanic o uno médico).
*   Usa `pgmpy` para aprender la estructura (Structure Learning) de los datos y luego estima sus parámetros. ¡Compara el grafo aprendido automáticamente con lo que tú habrías diseñado manualmente!

---

## Resumen de Mejores Prácticas

> [!TIP]
> **No te saltes las matemáticas:** Cada vez que el curso introduzca una ecuación compleja con sumatorios sobre conjuntos, escríbela en papel y resuélvela para un ejemplo de juguete (2 variables binarias).
> 
> **Código paralelo a la teoría:** Aunque el curso teórico use pseudocódigo o matemáticas puras, ten siempre un Jupyter Notebook abierto con `pgmpy` para replicar los ejemplos de las lecciones.
>
> **Honors Track:** Haz los ejercicios de programación. Leer sobre Belief Propagation no sirve de nada si no intentas implementar el paso de mensajes matricialmente.
