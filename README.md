<div align="center">

# 🧠 myLearnings

**Un monorepo de aprendizaje continuo: notas, laboratorios y experimentos sobre las tecnologías que voy explorando.**

De la teoría al `docker compose up`. Cada carpeta es un tema, y casi todo viene con algo que se puede ejecutar, romper y volver a levantar.

<!-- Badges -->
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat&logo=apachekafka&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=flat&logo=neo4j&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=flat&logo=apachespark&logoColor=white)

</div>

---

## 📖 Sobre este repositorio

`myLearnings` es mi cuaderno de bitácora técnico. En lugar de tener apuntes
sueltos por carpetas inconexas, reúno aquí todo lo que voy estudiando en un
único sitio versionado, mezclando **tres formatos**:

- 📝 **Notas y apuntes** — explicaciones propias de conceptos, escritas para
  entenderlos de verdad, no para copiarlos.
- 🧪 **Laboratorios reproducibles** — entornos con Docker / Kubernetes que se
  levantan en local para *ver* las cosas funcionar (o fallar).
- 🔬 **Investigación y prototipos** — papers, modelos semánticos y pruebas de
  concepto en fase exploratoria.

> La mayoría del contenido está en **español**, ya que es material de estudio
> personal. Pensado como referencia para futuros proyectos y para el trabajo.

---

## 🗂️ Áreas

| Área | Contenido | Estado |
| ---- | --------- | ------ |
| [☸️ Kubernetes](#️-kubernetes) | Preparación de la **CKA** y labs de autoescalado (HPA, VPA, KEDA) | 🟢 Activo |
| [📨 Messaging](#-messaging) | Sistemas de mensajería distribuida (Kafka, NATS) + observabilidad | 🟢 Activo |
| [🗄️ Databases](#️-databases) | Bases de datos en Docker y clientes Python (Postgres, Neo4j, SurrealDB) | 🟢 Activo |
| [🤖 IA](#-ia) | Modelos semánticos y modelado de conocimiento | 🟢 Activo |
| [🔐 Security](#-security) | Laboratorios de seguridad ofensiva/defensiva | 🟢 Activo |
| [🔄 Pipelines](#-pipelines) | Automatización de flujos con n8n | 🟡 En curso |
| [📊 MachineLearning](#-machinelearning) | Estadística bayesiana y modelos gráficos probabilísticos | 🟡 En curso |
| [🔬 ResearchDevelopment](#-researchdevelopment) | Papers, capa semántica y modelado de conocimiento | 🟡 En curso |
| [☁️ Azure](#️-azure) | Azure Functions con Python | 🟡 En curso |
| [⚡ BigData](#-bigdata) | Procesamiento distribuido con Spark | 🟡 En curso |
| [💻 Programming](#-programming) | Comparativas y notas de lenguajes | 🟡 En curso |

---

## ☸️ Kubernetes

Preparación de la certificación **CKA** y laboratorios prácticos de
autoescalado.

- **CKA/** — Apuntes por dominios del examen: mantenimiento de cluster, ciclo
  de vida de aplicaciones (HPA en profundidad) y *scheduling* (afinidades,
  taints/tolerations, admission controllers, Volcano).
- **Labs/k8s-autoscaling-lab/** — Lab completo sobre `kind` que cubre
  `metrics-server`, **HPA**, **VPA** y **KEDA** con NATS como fuente de
  eventos. Cada paso tiene su manifiesto y su script de instalación.

## 📨 Messaging

Aprendizaje y experimentación con **sistemas de mensajería distribuidos**,
abordados desde tres ángulos: infraestructura, métricas/rendimiento y
desarrollo de aplicaciones.

- Despliegue local de **Apache Kafka** (imágenes de Confluent) y **NATS**.
- Stack de **observabilidad** listo para comparar tecnologías: Prometheus,
  Grafana, OpenSearch y Fluent Bit.
- Targets duales (Docker Compose y Kubernetes) para comparar la operación.

## 🗄️ Databases

- **docker-databases/** — Stacks de Docker Compose listos para usar:
  **PostgreSQL**, **Neo4j** y **SurrealDB**.
- **python_db_clients/** — Demos de clientes Python (gestionado con `uv`) para
  cada motor.
- **GraphDatabases/** — Primeros pasos con **Neo4j**: seeds en Cypher, consultas
  de recomendación y cálculo de similitud.

## 🤖 IA

Exploración de **modelos semánticos** y modelado de conocimiento aplicado al
análisis de repositorios.

- Filosofía y fundamentos de los modelos semánticos.
- Modelo de repositorios y pipeline de agente extractor.
- Esquema JSON del modelo semántico y mapa de modelado de conocimiento.

## 🔐 Security

Laboratorios prácticos de seguridad.

- **paramiko-ssh-mitm-lab/** — Lab reproducible con Docker Compose que
  demuestra por qué `paramiko.AutoAddPolicy()` es inseguro: un ataque **MITM**
  sobre SSH/SFTP y cómo el *pinning* de host key lo mitiga. Incluye runbook,
  cliente vulnerable vs. seguro y tests automáticos.

## 🔄 Pipelines

- **n8n/** — Automatización de flujos de trabajo: fundamentos, despliegue con
  Docker e integraciones (p. ej. GitHub → Event Hub).

## 📊 MachineLearning

Modelos y ejemplos de código para aprender **Machine Learning** y **Deep
Learning**.

- Roadmap de **Estadística Bayesiana**.
- **Modelos Gráficos Probabilísticos** con su plan de estudio.

## 🔬 ResearchDevelopment

Material más exploratorio y académico.

- **Papers/** — Lecturas de referencia (Adam, anotación semántica con LLMs…).
- **SemanticLayer/** y **KnowledgeModelling/** — Notas sobre capa semántica,
  unidades semánticas y modelado de conocimiento (de los textos en crudo a los
  apuntes mejorados).
- **TestingLean/** — Experimentos con el demostrador de teoremas **Lean**.

## ☁️ Azure

- **AzureFunctions/** — Proyecto de **Azure Functions** en Python con su
  configuración de desarrollo.

## ⚡ BigData

- **Spark/** — Notas sobre el modelo de procesamiento **distribuido** de Apache
  Spark.

## 💻 Programming

- Comparativas y notas de lenguajes (p. ej. **Zig vs. Rust**).

---

## 🚀 Cómo usarlo

No hay un único punto de entrada: cada área es independiente. La forma
recomendada de navegar es:

```bash
git clone https://github.com/pablocuestagarcia/myLearnings.git
cd myLearnings
```

A partir de ahí, entra en la carpeta del tema que te interese y lee su
`README.md` propio. Los laboratorios con código suelen incluir sus propias
instrucciones de arranque (normalmente `docker compose up` o un script en
`scripts/`).

---

## 🧭 Filosofía

> *"No leerlo en un blog, verlo en un log."*

Aprender haciendo. Siempre que puedo, prefiero un entorno que se pueda levantar
y observar antes que un resumen teórico. Por eso muchas carpetas no son solo
apuntes, sino laboratorios que se pueden ejecutar de principio a fin.

---

<div align="center">

📚 *Repositorio de aprendizaje personal — en evolución constante.*

</div>
