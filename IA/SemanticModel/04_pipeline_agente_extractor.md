# Pipeline de Extracción: El Agente Autónomo

Para poblar nuestro Modelo Semántico Corporativo necesitamos analizar miles de repositorios. Sin embargo, procesar repositorios enteros mediante LLMs (*Large Language Models*) presenta tres problemas críticos:

1.  **Coste Económico:** Alimentar a un modelo con 20.000 líneas de código puede costar entre 0.50$ y 1.00$ por repositorio, haciendo insostenible la integración continua.
2.  **El problema del Ruido (*Lost in the Middle*):** Los LLMs pierden el contexto si se les inyecta demasiada información irrelevante (*boilerplate*, tests unitarios, dependencias de terceros), empeorando su capacidad analítica.
3.  **Heterogeneidad de Lenguajes:** Un script estático que busca un `package.json` fallará irremediablemente al analizar repositorios en C++ (`CMakeLists.txt`), Rust (`Cargo.toml`) o R (`DESCRIPTION`).

La solución a estos problemas no es un script determinista, sino un **Flujo Agéntico (Agentic Workflow)**. 

En lugar de inyectar código de forma pasiva a un LLM, desplegamos un "Agente Autónomo" dotado de herramientas (*Tools/Function Calling*) al que le delegamos la siguiente misión: *"Entra en este repositorio, explóralo gastando el menor número de tokens posible, descubre su ecosistema y devuélveme un JSON semántico"*.

## Fases del Flujo Agéntico

El agente opera en un ciclo de observación y acción estructurado en cuatro fases:

### 1. Fase de Reconocimiento (Mapeo Inicial)
El agente no lee código en primera instancia. Su primera acción es utilizar una herramienta de sistema (ej. `tree` o `list_directory`) para escanear la estructura de carpetas de alto nivel.
*   **Coste:** ~100-200 tokens.
*   **Decisión Autónoma:** Al ver `CMakeLists.txt` y una carpeta `/include`, el agente deduce inmediatamente que está ante un ecosistema C/C++, ajustando su estrategia de lectura.

### 2. Fase de Extracción Específica (Golden Context)
Sabiendo en qué ecosistema se encuentra, el agente decide de forma autónoma qué archivos debe abrir para extraer la "arquitectura y capacidades" sin leer la lógica de negocio profunda.
*   **Lectura selectiva:** Abre el `README.md` (para inferir Intención y Dominio) y el archivo de manifiesto correspondiente (ej. `pom.xml`, `package.json`, `DESCRIPTION` en R) para identificar Infraestructura y Herramientas.
*   **Coste:** ~2.000 tokens (El "Contexto Dorado").

### 3. Fase de Indagación Profunda (Opcional y Dinámica)
Si tras la Fase 2 el agente considera que el dominio no está claro (por ejemplo, porque el README está vacío), puede invocar herramientas de búsqueda semántica (ej. `grep_search`).
*   **Acción:** El agente busca patrones arquitectónicos (`query="api"`, `query="model.fit"`, `query="Kafka"`). Si detecta un archivo llamado `src/fraud_detection_model.R`, el agente decide abrir ese archivo específico para confirmar sus sospechas.
*   Esto asegura resiliencia extrema frente a repositorios mal documentados o con estructuras caóticas (muy común en proyectos científicos de R o Python de un solo archivo).

### 4. Fase de Síntesis y Generación (Structured Output)
Con toda la información recopilada en su memoria a corto plazo, el agente entra en su fase final. Se le inyecta el *JSON Schema* estricto de nuestro Modelo Canónico y se le obliga a mapear todo su conocimiento adquirido a los campos estandarizados (Intención, Dominio, Capacidades).

## Beneficios del Enfoque Agéntico

1.  **Reducción de Costes del 95%:** Al leer únicamente el "Contexto Dorado", el escaneo de un repositorio masivo pasa de costar 1$ a costar apenas 0.02$, permitiendo escaneos diarios y manteniendo la Matriz Bayesiana siempre actualizada.
2.  **Agnosticismo Total:** El agente navega por instinto arquitectónico. No importa si mañana la empresa adopta un nuevo lenguaje de programación; el agente sabrá explorarlo usando la lista de directorios.
3.  **Precisión Quirúrgica:** Al eliminar el ruido del código fuente crudo, el agente focaliza su razonamiento lógico únicamente en los metadatos de alto nivel, mejorando drásticamente el acierto en la inferencia del Dominio y la Intencionalidad.
