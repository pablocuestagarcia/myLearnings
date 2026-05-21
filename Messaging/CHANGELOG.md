# Changelog

Cambios relevantes del playground de **Messaging**. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Las fechas
son `YYYY-MM-DD`.

## [Unreleased]

Trabajo previsto siguiendo el [ROADMAP](./ROADMAP.md).

### Por hacer (corto plazo)

- Cerrar **Fase 0.K**: paridad de la base sobre Kubernetes (kind +
  `kube-prometheus-stack` + `opensearch-operator` + fluent-bit chart +
  Strimzi + Redpanda Console).
- **Fase 1.1**: Schema Registry en Docker y Kubernetes.
- **Fase 3**: línea base de rendimiento (`kafka-*-perf-test`).

---

## [0.4.0] — 2026-05-13 — Diferenciación Docker / Kubernetes

### Added
- Nueva estructura por target de despliegue:
  - [Infra/docker/](./Infra/docker/) — contenido existente (Compose).
  - [Infra/kubernetes/](./Infra/kubernetes/) — placeholders para el target k8s.
- [Infra/docker/README.md](./Infra/docker/README.md) con la secuencia de
  arranque específica del target Compose.
- [Infra/kubernetes/README.md](./Infra/kubernetes/README.md) con el plan
  para el target Kubernetes: `kind` local, `Strimzi` para Kafka,
  `kube-prometheus-stack`, `opensearch-operator`, fluent-bit Helm chart
  y NATS Helm chart oficial.
- Política de **Helm charts y operators auditados** (añadida a la
  política de imágenes existente).
- Comparativa exhaustiva Docker vs Kubernetes en [Infra/README.md](./Infra/README.md):
  discovery, persistencia, scrape de métricas, recolección de logs,
  configuración y operación.

### Changed
- [Messaging/README.md](./README.md): introduce los dos targets y el
  nuevo árbol del repositorio.
- [OVERVIEW.md](./OVERVIEW.md): cada capítulo (stack Kafka,
  observabilidad, métricas, logs) incluye tabla `Docker | Kubernetes`.
- [ROADMAP.md](./ROADMAP.md) reorganizado: cada fase pasa a tener
  secciones `D` (Docker), `K` (Kubernetes) y/o `Común`. Se añade
  **Fase 0.K** como prerrequisito antes de avanzar.
- Las pruebas de rendimiento (fase 3) se ejecutan en ambos targets con
  el mismo formato de resultados.

### Moved
- `Infra/observability/` → `Infra/docker/observability/`.
- `Infra/kafka/` → `Infra/docker/kafka/`.

---

## [0.3.0] — 2026-05-13 — Roadmap y pruebas de rendimiento

### Added
- [ROADMAP.md](./ROADMAP.md) con 10 fases (F0–F9), checklists y criterio
  de aceptación por fase:
  - **F3** dedicada a **pruebas de rendimiento** (`kafka-producer-perf-test`,
    `kafka-consumer-perf-test`, `nats bench`): matriz de variables,
    métricas a capturar y dashboards reproducibles.
  - **F5** seguridad: CA local, TLS y mTLS, SASL/SCRAM, ACLs, OIDC con
    Keycloak.
  - **F6** réplicas/HA en Kafka (3 brokers KRaft), NATS (`R=3`) y
    OpenSearch multi-nodo.
  - **F7** backups y DR: MirrorMaker 2, mirroring de JetStream, snapshots
    a MinIO, snapshots de Prometheus.
  - **F8** gestión de secretos con Vault o `sops`/age.
  - **F9** hardening final y SLOs.
- Orden de prioridad recomendado al final del roadmap.

---

## [0.2.0] — 2026-05-13 — Documentación primero y consolidación

### Added
- [OVERVIEW.md](./OVERVIEW.md) como documento consolidado que resume
  todos los README individuales y define los dos ejes de los siguientes
  pasos (desarrollador y plataforma).
- [Infra/README.md](./Infra/README.md) con estrategia común, topología
  ASCII y secuencia de arranque.
- Pipelines de **métricas** y **logs** documentados con diagramas, tablas
  de exporters por tecnología y pasos para añadir un broker nuevo, en
  [Infra/docker/observability/README.md](./Infra/docker/observability/README.md).
- Política de **imágenes auditadas** en
  [Messaging/README.md](./README.md): solo imágenes oficiales del
  proyecto, del proveedor comercial de referencia o de fundaciones
  reconocidas (CNCF, Apache, Fluent).

### Changed
- Stack de Kafka migrado a imágenes auditadas:
  - Broker: `bitnami/kafka:3.7` → **`confluentinc/cp-kafka:7.7.1`**
    (Confluent, proveedor de referencia).
  - UI: `provectuslabs/kafka-ui:latest` → **`docker.redpanda.com/redpandadata/console:v2.7.2`**.
  - Exporter: `danielqsj/kafka-exporter:latest` →
    **`docker.redpanda.com/redpandadata/kminion:v2.2.12`** (expone
    consumer lag y latencia end-to-end).
- Versiones **pinadas** en todos los componentes críticos (sin `latest`).
- Configuración de Prometheus actualizada para *scrapear* `kafka-kminion:8080`.
- Kafka en KRaft con `CLUSTER_ID` fijo, healthcheck con `kafka-topics`
  y JMX habilitado por si se añade un JMX exporter más adelante.

---

## [0.1.0] — 2026-05-13 — Base inicial del playground

### Added
- Estructura inicial bajo `Messaging/Infra/` con dos stacks de Docker Compose:
  - **kafka/**: broker Kafka en modo KRaft (sin Zookeeper), Kafka UI y
    exporter Prometheus.
  - **observability/**: Prometheus + Grafana (con datasources
    provisionados), OpenSearch + Dashboards y Fluent Bit recolectando
    logs de `/var/lib/docker/containers/*.log`.
- Red Docker externa compartida `messaging-net` para que los dos stacks
  se descubran por nombre de servicio.
- READMEs por subdirectorio con instrucciones de arranque y smoke tests.
