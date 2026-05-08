# Mapa Conceptual: Modelado del Conocimiento e Inteligencia Artificial

Si tu objetivo principal es el **Modelado del Conocimiento**, has elegido una combinación de temas fascinante y perfectamente conectada. Aquí te explico qué es cada cosa y cómo encajan juntas como piezas de un rompecabezas.

---

## 1. Ontologías (El Modelado Lógico y Estricto)
**¿Qué son?** En Filosofía, la ontología estudia "lo que existe". En Inteligencia Artificial, una ontología es una **representación formal e interpretable por máquinas** de un dominio de conocimiento. Define qué entidades existen, sus propiedades y cómo se relacionan entre sí.
*   **Ejemplo:** En una ontología médica, defines que `[Gripe] es_un [Virus]` y que `[Gripe] tiene_sintoma [Fiebre]`.   
*   **Características:** Son deterministas (basadas en lógica de primer orden). No manejan bien la incertidumbre. Si la ontología dice que los pájaros vuelan, y le presentas un pingüino, el sistema lógico "se rompe" a menos que programes excepciones explícitas.
*   **Herramientas:** Lenguajes como OWL / RDF y editores como Protégé.

## 2. Estadística Bayesiana (El Lenguaje de la Incertidumbre)
**¿Qué es?** Es un paradigma de la estadística completamente diferente a la estadística clásica (frecuentista). En la estadística bayesiana, la probabilidad no es "la frecuencia con la que ocurre un evento", sino el **grado de creencia (certidumbre)** que tenemos sobre algo antes de ver los datos (A Priori), y cómo esa creencia **se actualiza** (A Posteriori) cuando observamos nueva evidencia.
*   **Ejemplo:** Tu creencia *A Priori* de tener una enfermedad rara es 0.001%. Si una prueba médica da positivo (Evidencia), usas el Teorema de Bayes para *actualizar* tu creencia. Ahora tu probabilidad *A Posteriori* podría ser del 5%.
*   **En el Modelado del Conocimiento:** Es vital porque el conocimiento humano en el mundo real rara vez es del 100%. La estadística bayesiana nos da las matemáticas para modelar el "yo creo que esto es así, con un 85% de seguridad".

## 3. Probabilistic Graphical Models - PGMs (La Unión Perfecta)
**¿Qué son?** Aquí es donde la Ontología y Bayes se dan la mano. Los PGMs combinan la teoría de grafos (usada en las ontologías para modelar relaciones estructurales) con la estadística bayesiana (para manejar la incertidumbre).
*   En lugar de decir `[Gripe] causa [Fiebre]` (Ontología estricta).
*   Dices: `[Gripe] -> [Fiebre]` (Grafo) y le añades matemáticas: `P(Fiebre | Gripe) = 0.8` (Estadística Bayesiana).
*   **Por qué importa:** Los PGMs son la forma más robusta y matemáticamente pura de hacer **Modelado del Conocimiento Experto** tolerante a fallos y a información incompleta.

## 4. Metaheurísticas (La Fuerza Bruta Inteligente)
**¿Qué son?** Son algoritmos de optimización diseñados para encontrar "soluciones suficientemente buenas" en problemas que son imposibles de resolver con cálculo exacto porque hay billones de combinaciones (problemas NP-Hard). Están inspiradas en la naturaleza.
*   **Ejemplos:** Algoritmos Genéticos (evolución natural), Optimización por Enjambre de Partículas (bandadas de pájaros), o Simulated Annealing (enfriamiento de metales).
*   **¿Cómo se relaciona con el Modelado del Conocimiento y PGMs?** 
    *   Imagina que tienes una base de datos gigante y quieres que el ordenador deduzca automáticamente la "Ontología probabilística" (el grafo del PGM). 
    *   Existen más grafos posibles que átomos en el universo. Es imposible probarlos todos. Usamos **Metaheurísticas** (como Algoritmos Genéticos) para "navegar" ese espacio infinito y encontrar el grafo (el modelo de conocimiento) que mejor explica tus datos.

---

## Tu Camino de Aprendizaje Sugerido

1.  **Fundamento de Creencias:** Empieza con **Estadística Bayesiana** pura (Teorema de Bayes, Priors, Posteriors). Cambiará tu forma de ver el mundo y los datos.
2.  **Estructura Estricta:** Dedica 2-3 días a leer sobre **Ontologías** y la Web Semántica para entender cómo se mapea el conocimiento de forma determinista usando grafos.
3.  **El Sistema Principal:** Ahora entra de lleno a los **Cursos de PGMs**. Verás que es simplemente la evolución natural (probabilística) de las ontologías, propulsada por la estadística bayesiana.
4.  **Optimización:** Deja las **Metaheurísticas** para el final. Cuando en el Curso 3 de PGMs (Learning) te pregunten *"¿Cómo buscamos el mejor grafo posible?"*, ahí es donde aplicarás los algoritmos genéticos o heurísticos.
