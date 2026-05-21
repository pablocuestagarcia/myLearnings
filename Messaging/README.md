# Messaging Playground

Espacio de aprendizaje y experimentación con sistemas de mensajería
distribuidos. Está pensado para abordar el tema desde **tres ángulos**, no
solo desde el desarrollo de aplicaciones:

1. **Infraestructura** — cómo se despliega, configura y opera cada broker
   en local. Topología, listeners, persistencia, healthchecks.
2. **Métricas y rendimiento** — instrumentación común para poder comparar
   tecnologías bajo cargas similares (latencias, throughput, consumer lag,
   uso de recursos).
3. **Desarrollo de aplicaciones** — productores, consumidores y patrones
   típicos (pub/sub, colas durables, streams) en distintos lenguajes.

## Tecnologías

| Tecnología       | Estado   | Descripción |
| ---------------- | -------- | ----------- |
| **Apache Kafka** | en curso | Log distribuido, alta durabilidad y throughput. Imágenes oficiales de Confluent. |
| **NATS**         | pendiente | Mensajería ligera con JetStream para persistencia. Imagen oficial NATS. |

## Targets de despliegue

Cada tecnología se despliega en **dos targets distintos**, en paralelo,
para poder comparar la experiencia de operación:

| Target | Carpeta | Para qué sirve |
| ------ | ------- | -------------- |
| **Docker Compose** | [Infra/docker/](./Infra/docker/) | Punto de partida rápido. Imágenes oficiales montadas a mano, todo en una sola red Docker. Bueno para entender cada pieza por separado. |
| **Kubernetes** (local con kind) | [Infra/kubernetes/](./Infra/kubernetes/) | Equivalente operacional con *operators* y *Helm charts*. Permite practicar la operación realista (rolling updates, réplicas, ConfigMaps, ServiceMonitors). |

La política de "imagen auditada" se aplica también a los **charts y
operators** del target Kubernetes (Strimzi para Kafka, kube-prometheus-stack,
opensearch-operator, fluent-bit chart, NATS Helm chart oficial).

## Política de imágenes y charts

Solo se usan artefactos con trazabilidad clara:

- **Imágenes**: oficiales del proyecto, del proveedor comercial de
  referencia (Confluent para Kafka) o de una fundación reconocida (CNCF,
  Apache, Fluent, …). Versión pinada en todos los manifiestos críticos.
- **Helm charts / operators**: del propio proyecto o de comunidades
  oficiales (`prometheus-community`, `nats-io`, `strimzi`,
  `opensearch-project`, `fluent`).

Se evitan imágenes y charts de terceros sin mantenimiento claro.

## Estructura del repositorio

```
Messaging/
├── README.md                # Este documento
├── OVERVIEW.md              # Documento consolidado
├── ROADMAP.md               # Plan por fases (ambos targets)
└── Infra/
    ├── README.md            # Estrategia común + comparativa Docker vs k8s
    ├── docker/              # Target 1 — Docker Compose
    │   ├── observability/
    │   ├── kafka/
    │   └── nats/            # pendiente
    └── kubernetes/          # Target 2 — Kubernetes (kind)
        ├── observability/   # pendiente
        ├── kafka/           # pendiente
        └── nats/            # pendiente
```

## Cómo empezar

- Camino rápido (Docker): seguir [Infra/docker/README.md](./Infra/docker/README.md).
- Camino k8s: seguir [Infra/kubernetes/README.md](./Infra/kubernetes/README.md)
  (en construcción).

Antes de tocar cualquier broker, levantar **siempre primero** el plano de
observabilidad del target correspondiente.
