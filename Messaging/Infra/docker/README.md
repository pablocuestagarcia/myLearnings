# Infra · Docker target

Variante de la infraestructura desplegada en local con **Docker Compose**.
La equivalente sobre Kubernetes vive en [../kubernetes/](../kubernetes/).

> Esta carpeta contiene **solo** los stacks de Docker. Decisiones
> transversales (objetivos, política de imágenes/charts, comparativa
> entre targets) están en [../README.md](../README.md).

## Contenido

```
Infra/docker/
├── observability/   # Prometheus + Grafana + OpenSearch + Fluent Bit (compartido)
├── kafka/           # cp-kafka (KRaft) + Redpanda Console + kminion
└── nats/            # (pendiente)
```

Cada subdirectorio es auto-contenido: su propio `docker-compose.yml` y
su `README.md`.

## Red compartida

Todos los stacks se conectan a la red Docker externa `messaging-net`,
para que el plano de observabilidad alcance los exporters por DNS de
servicio (`kafka-kminion:8080`, `nats-exporter:7777`, …) sin exponer
puertos al host.

## Secuencia de arranque

```bash
# 1) Red compartida (solo la primera vez)
docker network create messaging-net

# 2) Plano común de observabilidad
cd observability && docker compose up -d

# 3) Broker que se quiera probar
cd ../kafka && docker compose up -d
```

Apagado: `docker compose down` (con `-v` para borrar volúmenes).
