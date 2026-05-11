# Principios Filosóficos del Modelo Semántico

Este documento establece los principios teóricos fundamentales que guían el diseño de nuestro modelo semántico de repositorios. Para que el ecosistema sea gobernable, escalable y verdaderamente útil a nivel analítico, debe adherirse a los siguientes dos axiomas: uno arquitectónico y otro matemático.

## 1. El Axioma Arquitectónico: Representar vs. Reproducir

El error más común al diseñar catálogos de software internos (*Developer Portals*) es confundir el objetivo del modelo. Debemos mantener una distinción estricta entre un modelo diseñado para *reproducir* y un modelo diseñado para *representar*.

### Modelo para Reproducir (Generativo / Determinista)
*   **Objetivo:** Clonar, instanciar o recrear el esqueleto del software para que sea ejecutable o desplegable.
*   **Naturaleza:** Prescriptivo, exhaustivo y enfocado en la implementación técnica (el "Cómo").
*   **Artefactos Típicos:** Plantillas de *Yeoman*, *Helm Charts*, Módulos de *Terraform*, especificaciones OpenAPI estrictas, *Archetypes* de Maven.
*   **Símil:** Son los **planos arquitectónicos de construcción** de una casa. Contienen la medida exacta de cada tubería, el grosor de los muros y el calibre del cableado eléctrico.
*   **El Antipatrón Analítico:** Si intentamos utilizar "planos de tuberías" para buscar "casas con estilo minimalista", fracasaremos. El exceso de ruido técnico (versiones precisas de dependencias, variables de entorno, configuraciones de red locales) oscurece completamente la visión estratégica de alto nivel.

### Modelo para Representar (Semántico / Analítico)
*   **Objetivo:** Comprender, clasificar, buscar y descubrir relaciones entre repositorios dentro de un gran ecosistema corporativo.
*   **Naturaleza:** Descriptivo, abstracto y deliberadamente ***lossy*** (diseñado con pérdida de información). Ignora el código *boilerplate* y las particularidades de despliegue para centrarse en la Intención (el "Por qué") y las Capacidades (el "Qué").
*   **Artefactos Típicos:** Documentos JSON Semánticos, Grafos de Conocimiento, Ontologías de Arquitectura Empresarial.
*   **Símil:** Es el **anuncio inmobiliario** de la casa ("Chalet de 3 habitaciones, estilo moderno, cerca de la playa"). Resulta imposible construir una casa a partir de un simple anuncio, pero es la abstracción perfecta para que un humano (o un algoritmo de búsqueda) la encuentre, la compare con otras y entienda su propósito fundamental.

**Conclusión Estratégica:** Nuestro modelo semántico debe resistir siempre la tentación de descender al nivel del código exacto o la configuración de despliegue. Su valor reside exclusivamente en su capacidad de **abstraer**.

---

## 2. El Axioma Matemático: Razonamiento Bayesiano bajo Incertidumbre

Cuando analizamos repositorios de código (incluso si utilizamos herramientas de parsing estático o LLMs avanzados), nunca obtenemos certezas absolutas, únicamente probabilidades basadas en pistas estructurales. Por tanto, el motor de análisis y la base matemática de nuestro modelo no deben asentarse sobre una lógica booleana estricta o estática, sino sobre la **Estadística Bayesiana**.

El Teorema de Bayes nos proporciona el marco riguroso para actualizar nuestras "creencias" (clasificaciones) a medida que observamos nueva evidencia empírica en el código:

$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$

### Aplicación Práctica al Modelo Semántico

**1. Inferencia Algorítmica de Intenciones:**
Imaginemos que el motor de extracción está escaneando un nuevo repositorio para inferir si su Intención de Dominio ($A$) pertenece al "Procesamiento de Pagos".
*   **Prior $P(A)$ (Creencia Previa):** Antes de leer un solo archivo, ¿qué probabilidad existe de que sea un sistema de pagos? Si históricamente en la empresa hay 1000 repositorios y solo 20 son de pagos, la probabilidad base (*Prior*) es muy baja: 2%.
*   **Evidence $B$ (Evidencia Técnica):** El escáner detecta que el repositorio importa la librería externa `stripe-java`, requiere una base de datos relacional y posee configuraciones criptográficas fuertes.
*   **Likelihood $P(B|A)$ (Verosimilitud):** Basado en la matriz histórica de la empresa, la probabilidad de que un "sistema de pagos" legítimo utilice *Stripe* y criptografía es altísima (ej. 90%).
*   **Posterior $P(A|B)$ (Inferencia Final):** El motor bayesiano cruza estos datos matemáticamente y concluye: "Dada la presencia simultánea de Stripe y alta criptografía, actualizo mi creencia inicial del 2% y dictamino que existe un **96% de probabilidad** de que este repositorio pertenezca al dominio de Pagos".

**2. Aprendizaje Orgánico y Continuo (*Organic Learning*):**
El verdadero poder de una matriz bayesiana es que los **Priors se auto-actualizan**. 
Si la dirección tecnológica decide virar hacia arquitecturas orientadas a eventos, cada nuevo repositorio que se cree utilizando *Kafka* o *RabbitMQ* provocará que la probabilidad base general ($P(Event\_Driven)$) aumente en toda la compañía.
Cuando se evalúe el siguiente repositorio dentro de unos meses, el sistema Bayesiano será matemáticamente más propenso a inferir procesamiento asíncrono porque habrá "aprendido" que la cultura arquitectónica corporativa ha mutado. El modelo se mantiene "vivo" y se ajusta a la realidad sin necesidad de reescribir tediosas reglas de validación estáticas.

**3. Modelado Honesto de la Incertidumbre:**
El estado subyacente de nuestro modelo debe ser capaz de reflejar esta varianza estadística. En lugar de forzar a los algoritmos a emitir un veredicto determinista ciego (`"is_payment_gateway": true`), el grafo puede mantener una distribución de probabilidad real: `{"domain": {"payments": 0.96, "user_management": 0.04}}`. 
Esto es crítico para establecer umbrales de confianza automatizados (ej. "Solo autocompletar el JSON si el *Posterior* supera el 0.90; en caso contrario, notificar al *Tech Lead* para revisión manual").
