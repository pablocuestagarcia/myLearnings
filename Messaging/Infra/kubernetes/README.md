# Infra · Kubernetes target

Variante de la infraestructura desplegada sobre **Kubernetes** (local con
[kind](https://kind.sigs.k8s.io/)). Las mismas tecnologías que en
[../docker/](../docker/), pero usando *operators* y *Helm charts* en
lugar de Docker Compose.

> Pendiente de implementación. Este README fija el plan; los manifiestos
> y values se irán añadiendo siguiendo el [ROADMAP](../../ROADMAP.md).

## Cluster local

- **Distribución**: `kind` (Kubernetes en contenedores Docker).
- **Versión de control plane**: a fijar al crear el cluster (por ejemplo
  `kindest/node:v1.31.0`).
- **Topología**: empezamos con 1 nodo *control-plane* + 2 *workers* para
  poder probar `antiAffinity` y réplicas reales.
- **Ingress**: `ingress-nginx` (chart oficial) para exponer Grafana,
  OpenSearch Dashboards y Redpanda Console al host.

```bash
# Estructura mínima esperada
Infra/kubernetes/
├── README.md
├── cluster/                  # config de kind y bootstrap
│   └── kind-config.yaml
├── observability/            # kube-prometheus-stack + OpenSearch Operator + fluent-bit
├── kafka/                    # Strimzi: Kafka, KafkaNodePool, KafkaTopic, ...
└── nats/                     # NATS Helm chart (oficial)
```

## Componentes previstos (política de imágenes / charts)

| Pieza                       | Implementación en k8s                                                    | Origen |
| --------------------------- | ------------------------------------------------------------------------ | ------ |
| Kafka                       | **Strimzi** operator (CRDs `Kafka`, `KafkaNodePool`, `KafkaTopic`, `KafkaUser`). | CNCF (graduado 2024). |
| UI de Kafka                 | Redpanda Console vía su Helm chart oficial.                              | Redpanda Data. |
| Métricas de Kafka           | `KafkaExporter` integrado en Strimzi + `ServiceMonitor` para Prometheus. | Strimzi. |
| NATS                        | Helm chart oficial `nats-io/nats` con JetStream.                         | NATS.io. |
| Prometheus + Grafana + Alertmanager | `kube-prometheus-stack` (chart prometheus-community).            | CNCF prometheus-community. |
| OpenSearch + Dashboards     | `opensearch-operator` (CRDs `OpenSearchCluster`).                        | OpenSearch project. |
| Logs                        | `fluent/fluent-bit` Helm chart oficial con filtro `kubernetes`.          | Fluent (CNCF). |
| Secretos (fase posterior)   | `external-secrets-operator` + Vault, o `sops-secrets-operator`.          | CNCF / Mozilla. |

## Diferencias clave con el target Docker

| Aspecto          | Docker Compose                                | Kubernetes |
| ---------------- | --------------------------------------------- | ---------- |
| Aislamiento      | Red Docker `messaging-net`.                   | Namespace por componente (`kafka`, `nats`, `observability`). |
| Discovery        | Nombre del servicio en la red Compose.        | DNS cluster-local: `<svc>.<ns>.svc.cluster.local`. |
| Persistencia     | Volúmenes nombrados de Docker.                | `PersistentVolumeClaim` (StorageClass por defecto de kind). |
| Exposición al host | `ports:` en el compose.                     | `Service` + `Ingress` (o `NodePort` para casos puntuales). |
| Scrape métricas  | `static_configs` en `prometheus.yml`.         | `ServiceMonitor` / `PodMonitor` del Prometheus Operator. |
| Recolección logs | Fluent Bit lee `/var/lib/docker/containers`.  | Fluent Bit lee `/var/log/containers` + filtro `kubernetes`. |
| Configuración    | Variables de entorno en el compose.           | `ConfigMap` y `Secret`, montados o como `envFrom`. |
| Operación        | `docker compose up/down`, comandos manuales.  | CRDs del operator (rolling upgrade, reasignación, etc.). |

## Arranque previsto (a implementar)

```bash
# 1. Crear el cluster
kind create cluster --config cluster/kind-config.yaml --name messaging

# 2. Observabilidad (operators + Prometheus stack)
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n observability --create-namespace -f observability/kube-prometheus-stack.values.yaml
helm install opensearch-operator opensearch-operator/opensearch-operator \
  -n observability
helm install fluent-bit fluent/fluent-bit -n observability \
  -f observability/fluent-bit.values.yaml

# 3. Kafka (Strimzi)
helm install strimzi strimzi/strimzi-kafka-operator -n kafka --create-namespace
kubectl apply -n kafka -f kafka/kafka.yaml

# 4. NATS
helm install nats nats/nats -n nats --create-namespace -f nats/values.yaml
```

## Lo que NO debería divergir entre targets

Para que la comparación tenga sentido, mantenemos comunes:

- Versiones del software desplegado (mismo Kafka, mismo NATS, etc.).
- Métricas expuestas y nombres de los dashboards en Grafana.
- Convenciones de naming (índices `docker-logs-*` aquí se llamarán
  `k8s-logs-*` por claridad, pero los dashboards de logs serán reutilizables).
- Pruebas de rendimiento (ver fase 3 del [ROADMAP](../../ROADMAP.md)):
  los scripts se ejecutan contra los endpoints expuestos del cluster, sin
  importar el target.
