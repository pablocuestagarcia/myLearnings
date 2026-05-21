# Messaging Playground — Overview

Documento consolidado del mini-proyecto. Resume el contenido de los README
individuales y define la hoja de ruta para los siguientes pasos.

> Documentos de referencia:
> [Messaging/README.md](./README.md) ·
> [Infra/README.md](./Infra/README.md) ·
> [Infra/docker/README.md](./Infra/docker/README.md) ·
> [Infra/kubernetes/README.md](./Infra/kubernetes/README.md) ·
> [ROADMAP.md](./ROADMAP.md)

---

## 1. Objetivo

Aprender y comparar sistemas de mensajería distribuidos (Apache Kafka,
NATS, …) desde tres ángulos complementarios:

1. **Infraestructura** — despliegue, configuración y operación.
2. **Métricas y rendimiento** — instrumentación común que permita
   comparar tecnologías bajo cargas similares.
3. **Desarrollo de aplicaciones** — productores, consumidores y patrones
   en distintos lenguajes.

## 2. Dos targets de despliegue

El playground se despliega **en paralelo** sobre dos targets distintos.
La comparación entre ellos es deliberada y forma parte del aprendizaje.

| Target | Carpeta | Características |
| ------ | ------- | --------------- |
| **Docker Compose** | [Infra/docker/](./Infra/docker/) | Imágenes oficiales puestas a mano sobre una red Docker. Bueno para entender cada componente por separado. |
| **Kubernetes** (local con [kind](https://kind.sigs.k8s.io/)) | [Infra/kubernetes/](./Infra/kubernetes/) | Mismas tecnologías vía operators y Helm charts. Ciclo operacional realista: rolling updates, réplicas, CRDs. |

Comparativa detallada de los dos modelos (discovery, persistencia, scrape
de métricas, logs, …) en [Infra/README.md](./Infra/README.md).

## 3. Política de imágenes y charts

Solo se usan artefactos con trazabilidad clara:

- **Imágenes**: oficiales del proyecto, del proveedor comercial de
  referencia (Confluent para Kafka) o de una fundación reconocida
  (CNCF, Apache, Fluent, …).
- **Helm charts / operators**: del propio proyecto o de comunidades
  oficiales (`prometheus-community`, `nats-io`, `strimzi`,
  `opensearch-project`, `fluent`).
- Versión pinada en todos los manifiestos críticos; nada de `latest`.

## 4. Estructura

```
Messaging/
├── README.md              # Visión general
├── OVERVIEW.md            # Este documento
├── ROADMAP.md             # Plan por fases (Docker + Kubernetes)
└── Infra/
    ├── README.md          # Estrategia común y comparativa entre targets
    ├── docker/            # Target 1 — Docker Compose
    │   ├── observability/
    │   ├── kafka/
    │   └── nats/          # pendiente
    └── kubernetes/        # Target 2 — Kubernetes (kind)
        ├── observability/ # pendiente
        ├── kafka/         # pendiente
        └── nats/          # pendiente
```

## 5. Stack de Kafka

Misma versión de Kafka en los dos targets; lo que cambia es **cómo se
despliega**.

| Pieza | Docker | Kubernetes |
| ----- | ------ | ---------- |
| Broker        | Imagen `confluentinc/cp-kafka:7.7.1` en KRaft.        | Strimzi: `Kafka` CR + `KafkaNodePool`. |
| UI            | `redpandadata/console:v2.7.2`.                        | Redpanda Console (Helm chart oficial). |
| Exporter      | `redpandadata/kminion:v2.2.12`.                       | `KafkaExporter` de Strimzi + `ServiceMonitor`. |
| Topics, ACLs  | Comandos `kafka-topics`, `kafka-acls`.                | CRDs `KafkaTopic`, `KafkaUser`. |
| Exposición    | `localhost:9094` (listener `EXTERNAL`).               | `Service` + `Ingress` (o `NodePort`). |
| Persistencia  | Volumen Docker `kafka_data`.                          | `PersistentVolumeClaim`. |

Detalle del target Docker en [Infra/docker/kafka/README.md](./Infra/docker/kafka/README.md).
El target Kubernetes se irá poblando siguiendo el [ROADMAP](./ROADMAP.md).

## 6. Observabilidad

### 6.1 Pipeline de métricas

```
[broker] ── Kafka API ──► [exporter] ── /metrics ──► [Prometheus] ──► [Grafana]
                                          scrape         TSDB         dashboards
```

| Pieza             | Docker                                        | Kubernetes |
| ----------------- | --------------------------------------------- | ---------- |
| Exporter de Kafka | kminion (contenedor independiente).           | KafkaExporter integrado en Strimzi. |
| Descubrimiento    | `static_configs` en `prometheus.yml`.         | `ServiceMonitor` (Prometheus Operator). |
| Prometheus        | Imagen `prom/prometheus` + YAML.              | `kube-prometheus-stack` (Operator). |

### 6.2 Pipeline de logs

```
[contenedores] ──► [log driver / kubelet] ──► [Fluent Bit] ──► [OpenSearch] ──► [Dashboards]
```

| Pieza              | Docker                                         | Kubernetes |
| ------------------ | ---------------------------------------------- | ---------- |
| Origen de los logs | `/var/lib/docker/containers/*/*.log`.          | `/var/log/containers/*.log` del nodo. |
| Enriquecimiento    | Parser JSON.                                   | Parser JSON + filtro `kubernetes` (añade pod/namespace/labels). |
| Indexación         | Índice `docker-logs-YYYY.MM.DD`.               | Índice `k8s-logs-YYYY.MM.DD`. |
| OpenSearch         | Imagen `opensearchproject/opensearch`.         | `opensearch-operator` (`OpenSearchCluster` CR). |

### 6.3 Métricas relevantes

Comunes a los dos targets:

- `kafka_topic_partition_*`, `kafka_consumergroup_group_lag`.
- `kafka_broker_info`, `kafka_cluster_info`.
- `kminion_end_to_end_*` (latencia end-to-end medida produciendo y
  consumiendo un topic interno; clave para comparar tecnologías). En
  Strimzi se sustituirá por las métricas equivalentes del KafkaExporter.

## 7. Accesos rápidos (target Docker)

| URL                              | Componente              | Credenciales   |
| -------------------------------- | ----------------------- | -------------- |
| <http://localhost:9090>          | Prometheus              | —              |
| <http://localhost:3000>          | Grafana                 | `admin/admin`  |
| <http://localhost:5601>          | OpenSearch Dashboards   | —              |
| <http://localhost:8080>          | Redpanda Console (Kafka)| —              |
| <http://localhost:8081/metrics>  | kminion (Kafka exporter)| —              |

Los accesos del target Kubernetes dependerán del `Ingress` configurado;
se documentarán al implementarlo.

## 8. Arranque rápido

### 8.1 Target Docker

```bash
docker network create messaging-net
cd Infra/docker/observability && docker compose up -d
cd ../kafka && docker compose up -d
```

### 8.2 Target Kubernetes *(pendiente)*

```bash
kind create cluster --config Infra/kubernetes/cluster/kind-config.yaml --name messaging
# helm install ... (ver Infra/kubernetes/README.md)
```

## 9. Próximos pasos

Hoja de ruta detallada en [ROADMAP.md](./ROADMAP.md), organizada por
fases. Cada fase incluye su variante para los dos targets, y la fase 3
fija una **línea base de rendimiento** que se aplica a ambos sin
modificar los scripts.

Líneas principales:

- **Pista de desarrollador** (Kafka): Schema Registry, Avro/Protobuf,
  Connect, ksqlDB, Streams, transacciones, DLQ/outbox/Debezium.
- **Pista de plataforma** (Kafka): almacenamiento, particionado,
  listeners, cuotas, mantenimiento, upgrades.
- **Rendimiento**: `kafka-*-perf-test` y `nats bench`, mismos
  dashboards para comparar.
- **NATS**: paridad con Kafka y benchmarks comparables.
- **Seguridad, HA, backups, secretos**: lo que la base inicial dejó
  fuera; la mayor parte se aborda mejor en el target Kubernetes.
