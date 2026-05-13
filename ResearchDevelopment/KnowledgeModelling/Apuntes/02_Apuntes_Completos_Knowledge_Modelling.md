# Apuntes Completos: Introducción al Modelado de Conocimiento

El **Modelado de Conocimiento** es la disciplina orientada a capturar, organizar y representar formalmente la esencia y estructura de un dominio específico. Su propósito es lograr que tanto las personas como las máquinas puedan comprender y razonar sobre ese conocimiento.

---

## 1. De los Datos al Conocimiento (Jerarquía DIKW) y su Ciclo de Vida

Para entender la necesidad de modelar, debemos comprender cómo evoluciona la información:
*   **Datos:** Conjuntos independientes de caracteres y símbolos sin contexto.
*   **Información:** Datos dotados de un contexto explícito y un propósito, lo que les añade valor.
*   **Conocimiento:** Información combinada con habilidades y experiencia cognitiva, aplicada para lograr resultados. Se divide en:
    *   **Explícito:** Documentado, formal y fácil de compartir (ej. manuales).
    *   **Tácito:** Derivado de la experiencia personal e intuición, muy difícil de externalizar.
    *   **Implícito:** Reside en la mente, pero a diferencia del tácito, sí puede articularse y capturarse (ej. entrevistando a un experto).
*   **Sabiduría:** El conocimiento asimilado y validado a través del aprendizaje a largo plazo.

**Ciclo de Vida del Conocimiento:**
El conocimiento fluye a través de dos dimensiones conectadas:
1.  **Capa de Innovación:** Creación de conocimiento nuevo (ideación, modelado) hasta su salida al mercado o puesta en producción.
2.  **Capa de Compartición:** Identificación, organización, almacenamiento y difusión del conocimiento existente para la resolución de problemas y la toma de decisiones.

---

## 2. ¿Qué es un Modelo de Conocimiento o Ontología?

Si un *mapa mental* ayuda a un humano a estructurar ideas, un **Modelo de Conocimiento** (u Ontología) hace lo mismo pero con suficiente rigor formal para que las máquinas también lo entiendan.

*   **Definición de Gruber (1993):** "Una especificación explícita de una conceptualización".
*   **Definición de Studer (1997):** "Una especificación formal y explícita de una conceptualización compartida".
*   En la práctica, una ontología es el **plano arquitectónico** que define un "Dominio de Discurso".

**Perspectiva Filosófica:**
La ontología nació como la rama de la filosofía que estudia el "ser" y la "existencia" (qué significa existir, cómo agrupar entidades). La informática hereda este concepto para abstraer y estructurar dominios del mundo real.

---

## 3. Bloques de Construcción

La anatomía de una ontología se compone de los siguientes elementos:

1.  **Instancias (Individuos):** Ocurrencias específicas del mundo real (ej. *Harry Potter*, *Londres*, *Inglés*).
2.  **Relaciones (Propiedades):** Conexiones entre las instancias. 
    *   **Triple / Statement:** Es la unidad fundamental del conocimiento. Se compone de `Sujeto -> Relación -> Objeto` (ej. *Harry -> habla -> Inglés*).
3.  **Clases (Conceptos):** Agrupaciones lógicas o categorías que definen los requisitos para que un individuo pertenezca a ellas (ej. *Persona*, *País*, *Idioma*).
4.  **Taxonomía:** La estructura jerárquica en forma de árbol que organiza las clases.
    *   **Herencia Transitiva:** Es la magia de la taxonomía. Una clase hija (*Documento Financiero*) hereda todas las reglas y atributos de su clase padre (*Documento de Empresa*). Es crucial clasificar correctamente (por esencia, no por roles temporales como "estudiante" o "empleado").
5.  **Axiomas / Reglas:** Restricciones formales (ej. "Toda persona debe hablar al menos un idioma").

---

## 4. Representación y Lógica (Lightweight vs Heavyweight)

Los modelos pueden ser visuales (para humanos) o codificados (para máquinas).

*   **Lightweight Ontologies (Ligeras):** Asumen que el significado se entiende intuitivamente. Generalmente son representaciones visuales o jerarquías simples.
*   **Heavyweight Ontologies (Pesadas):** Codificadas con lenguajes lógicos formales para que los ordenadores puedan interpretar e inferir.

**Criterios de Elección de un Lenguaje Formal:**
1.  **Expresividad:** Variedad de estructuras disponibles para describir componentes (qué tanto puedo detallar).
2.  **Semántica:** Claridad e inequívoco en el significado de la especificación.
3.  **Rigor Matemático:** Capacidad para garantizar la **satisfacibilidad** (interpretación lógicamente verdadera) y la **coherencia** (ausencia de contradicciones).

**Lenguajes Comunes:**
*   Basados en Lógica Descriptiva (DL): **RDF** y **OWL** (Web Ontology Language, estándar actual por W3C).
*   Basados en Lógica de Primer Orden (FOL): **KIF** y **CL** (Common Logic).

---

## 5. Niveles de Abstracción

Las ontologías se clasifican según su generalidad y ámbito de aplicación:

1.  **Fundacionales / Superiores (Upper ontologies):** Capturan conceptos universales comunes a cualquier dominio (tiempo, espacio, objetos materiales). Requieren un enorme esfuerzo de estandarización.
    *   *Ejemplos:* SUMO, DOLCE, BFO, gist.
2.  **Nivel Medio (Middle level):** Dominio amplio, pero enfocadas a una temática reutilizable (ej. eventos en el tiempo, procesos de negocio). Sirven de puente.
    *   *Ejemplos:* PSL (Process Specification Language), The Zachman Framework.
3.  **Nivel de Usuario (User level):** Ultra-específicas para un entorno exacto (ej. tipos de motores a reacción en Boeing, jerarquía de departamentos en una oficina local). Son las que se construyen en el día a día para resolver problemas concretos.

---

## 6. Aplicaciones del Modelado de Conocimiento

El campo de aplicar estas estructuras a problemas reales se llama **Applied Ontology** y aporta beneficios incalculables:

*   **Interoperabilidad Semántica vs Integración:** La integración simplemente mueve datos de un sistema a otro; la interoperabilidad permite compartir datos conservando absolutamente su **contexto y significado**.
*   **Grafos de Conocimiento Empresarial (Enterprise Knowledge Graphs):** Bases de datos conectadas cuyo esquema es la ontología. Sirven para unificar perspectivas dispersas y permitir búsquedas y razonamientos complejos (ej. motores de recomendación, diagnósticos de fallos).
*   **Procesamiento de Lenguaje Natural (NLP):** Extraer relaciones, analizar sentimientos y comprender la intención gracias al contexto que aporta el modelo.
*   **Catálogos Semánticos y Data Management:** Ayuda en estrategias como *Data Mesh*, asegurando una gobernanza donde todos entienden lo mismo por los mismos términos.
*   **Linked Open Data:** Estructuración de grandes conjuntos de datos públicos (ej. DBpedia).
*   **Otras aplicaciones vitales:** Modelado de procesos de negocio, Gemelos Digitales (Digital Twins), recuperación semántica de documentos (Semantic Search), y abstracción de la complejidad en ecosistemas (cadenas de suministro, servicios financieros).
