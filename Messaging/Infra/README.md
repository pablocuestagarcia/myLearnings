# Infra — Estrategia común

Toda la infraestructura del playground se despliega en **dos targets**
distintos en paralelo:

| Target               | Carpeta                          | Estado     |
| -------------------- | -------------------------------- | ---------- |
| Docker Compose       | [docker/](./docker/)             | en curso   |
| Kubernetes (kind)    | [kubernetes/](./kubernetes/)     | pendiente  |

Aprender los dos en paralelo es uno de los objetivos del playground: la
misma tecnología tiene un ciclo de operación distinto según el target,
y la comparativa es deliberada.

## Tecnologías comunes

Independientemente del target, las tecnologías a desplegar son las mismas:

- Apache Kafka (broker + UI + exporter de métricas).
- NATS *(pendiente)*.
- Observabilidad: Prometheus, Grafana, OpenSearch, Fluent Bit.

Las **versiones del software** y las **métricas expuestas** se mantienen
alineadas entre targets para que la comparación sea honesta.

## Topología

### Target Docker

```
                 ┌────────────────────── messaging-net (Docker network) ────────────────────────┐
                 │                                                                              │
   ┌─────────────┴─────────────┐      ┌──────────────────────┐      ┌──────────────────────┐    │
   │ kafka stack               │      │ nats stack (TODO)    │      │ observability stack  │    │
   │  - cp-kafka (broker)      │      │  - nats              │      │  - prometheus        │    │
   │  - redpanda console (UI)  │      │  - nats-exporter     │      │  - grafana           │    │
   │  - kminion (exporter)     │      │                      │      │  - opensearch + UI   │    │
   └───────────────────────────┘      └──────────────────────┘      │  - fluent-bit        │    │
                                                                    └──────────────────────┘    │
                 └──────────────────────────────────────────────────────────────────────────────┘
```

- Discovery por nombre de contenedor en `messaging-net`.
- Logs leídos de `/var/lib/docker/containers/*/*.log`.
- Prometheus configurado con `static_configs`.

### Target Kubernetes

```
   ┌── ns: kafka ──────────────┐   ┌── ns: nats ─────────┐   ┌── ns: observability ──────────────┐
   │ Strimzi operator          │   │ NATS Helm release   │   │ kube-prometheus-stack             │
   │  └─ Kafka CR (broker pods)│   │  └─ JetStream pods  │   │  ├─ prometheus-operator + CRDs    │
   │     KafkaNodePool         │   │  └─ nats-exporter   │   │  ├─ grafana                       │
   │  └─ KafkaUser / Topic     │   │                     │   │  └─ alertmanager                  │
   │  Console (Helm chart)     │   │                     │   │ opensearch-operator               │
   │                           │   │                     │   │  └─ OpenSearchCluster CR          │
   │                           │   │                     │   │ fluent-bit DaemonSet              │
   └───────────────────────────┘   └─────────────────────┘   └───────────────────────────────────┘
                                       cluster: kind
```

- Discovery por DNS cluster-local: `<svc>.<ns>.svc.cluster.local`.
- Logs leídos del nodo: `/var/log/containers/*.log` + filtro `kubernetes`.
- Prometheus descubre targets vía `ServiceMonitor` / `PodMonitor`.

## Comparativa Docker vs Kubernetes

| Aspecto              | Docker Compose                              | Kubernetes |
| -------------------- | ------------------------------------------- | ---------- |
| Aislamiento de red   | Red Docker `messaging-net`.                 | Namespace por componente. |
| Discovery            | Nombre de servicio en la red Compose.       | DNS `<svc>.<ns>.svc.cluster.local`. |
| Persistencia         | Volúmenes nombrados de Docker.              | `PersistentVolumeClaim`. |
| Exposición al host   | `ports:` en el compose.                     | `Service` + `Ingress` (o `NodePort`). |
| Configuración        | `environment:` en el compose.               | `ConfigMap` y `Secret`. |
| Scrape de métricas   | `static_configs` en `prometheus.yml`.       | `ServiceMonitor` / `PodMonitor`. |
| Recolección de logs  | Fluent Bit lee `/var/lib/docker/containers`.| Fluent Bit lee `/var/log/containers` + filtro `kubernetes`. |
| Despliegue de Kafka  | `confluentinc/cp-kafka` directo.            | Strimzi operator (CRDs `Kafka`, `KafkaNodePool`, …). |
| Despliegue de Prom.  | Imagen `prom/prometheus` + YAML.            | `kube-prometheus-stack` (Operator + valores Helm). |
| Operación día-a-día  | `docker compose up/down`, comandos manuales.| CRDs del operator: rolling upgrade, reasignación, scaling. |

## Componentes por target

### Docker

| Servicio                | Imagen                                            |
| ----------------------- | ------------------------------------------------- |
| Kafka broker            | `confluentinc/cp-kafka:7.7.1`                     |
| Kafka UI                | `docker.redpanda.com/redpandadata/console:v2.7.2` |
| Kafka exporter          | `docker.redpanda.com/redpandadata/kminion:v2.2.12`|
| Prometheus              | `prom/prometheus:v2.54.1`                         |
| Grafana                 | `grafana/grafana:11.2.0`                          |
| OpenSearch              | `opensearchproject/opensearch:2.15.0`             |
| OpenSearch Dashboards   | `opensearchproject/opensearch-dashboards:2.15.0`  |
| Fluent Bit              | `fluent/fluent-bit:3.1.7`                         |

### Kubernetes

| Pieza                   | Implementación                                                       |
| ----------------------- | -------------------------------------------------------------------- |
| Cluster local           | `kind` (Kubernetes en contenedores Docker).                          |
| Ingress                 | `ingress-nginx` (chart oficial).                                     |
| Kafka                   | **Strimzi** operator (CRDs `Kafka`, `KafkaNodePool`, `KafkaTopic`, `KafkaUser`). |
| Kafka exporter          | `KafkaExporter` integrado en Strimzi + `ServiceMonitor`.             |
| Kafka UI                | Redpanda Console (Helm chart oficial).                               |
| NATS                    | `nats-io/nats` Helm chart oficial (con JetStream).                   |
| Prometheus + Grafana    | `kube-prometheus-stack` (chart `prometheus-community`).              |
| OpenSearch + Dashboards | `opensearch-operator` (CRDs `OpenSearchCluster`).                    |
| Fluent Bit              | `fluent/fluent-bit` Helm chart con filtro `kubernetes`.              |
| Secretos *(fase 8)*     | `external-secrets-operator` + Vault, o `sops-secrets-operator`.      |

## Secuencia de arranque

Ver el README de cada target:

- Docker → [docker/README.md](./docker/README.md).
- Kubernetes → [kubernetes/README.md](./kubernetes/README.md).

## Alcance del playground

El target Docker es deliberadamente sencillo (un solo nodo, sin TLS, sin
autenticación). El target Kubernetes es donde se irán incorporando las
piezas "de verdad" — TLS, mTLS, réplicas, backups, secretos — siguiendo
el [ROADMAP](../ROADMAP.md), porque el ecosistema k8s tiene operators y
charts ya diseñados para todo eso y el coste de adoptarlos es razonable.
