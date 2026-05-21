# Observabilidad común (Prometheus + Grafana + OpenSearch)

Stack compartido para todos los playgrounds de `Messaging` (Kafka, NATS, …).
Cubre dos planos: **métricas** (Prometheus + Grafana) y **logs**
(Fluent Bit + OpenSearch + OpenSearch Dashboards).

## Servicios

| Servicio                | Imagen                                        | Puerto host | Rol |
| ----------------------- | --------------------------------------------- | ----------- | --- |
| `prometheus`            | `prom/prometheus:v2.54.1`                     | `9090`      | TSDB + scraper de métricas. |
| `grafana`               | `grafana/grafana:11.2.0`                      | `3000`      | UI de dashboards (métricas y logs). |
| `opensearch`            | `opensearchproject/opensearch:2.15.0`         | `9200`      | Motor de almacenamiento y búsqueda de logs. |
| `opensearch-dashboards` | `opensearchproject/opensearch-dashboards:2.15.0` | `5601`   | UI de OpenSearch. |
| `fluent-bit`            | `fluent/fluent-bit:3.1.7`                     | —           | Recolector de logs (lee Docker, envía a OpenSearch). |

> ⚠️ Entorno **de desarrollo**: OpenSearch sin TLS ni autenticación,
> Grafana con `admin/admin`, retención corta. No reutilizar en producción.

---

## 1. Métricas — pipeline pull (Prometheus)

```
   [broker]                [exporter]              [prometheus]            [grafana]
  cp-kafka ──── Kafka API ──► kminion ── /metrics ──► scrape (15s) ──► PromQL queries
                              (:8080)                  storage TSDB        dashboards
```

- **Modelo pull**: Prometheus consulta periódicamente (`scrape_interval: 15s`)
  el endpoint `/metrics` de cada exporter. Los brokers **no envían** nada.
- Los exporters viven en la red Docker `messaging-net` y se resuelven por
  su nombre de servicio (`kafka-kminion:8080`, `nats-exporter:7777`, …).
  No es necesario exponer puertos al host para que Prometheus los alcance.
- La configuración de scrape vive en
  [prometheus/prometheus.yml](./prometheus/prometheus.yml). Cada broker se
  añade como un `job` independiente.

### Qué exporter usa cada tecnología

| Tecnología | Exporter                                      | Endpoint interno              | Qué expone (resumen) |
| ---------- | --------------------------------------------- | ----------------------------- | -------------------- |
| Kafka      | `redpandadata/kminion`                        | `kafka-kminion:8080/metrics`  | Topics, consumer lag, broker info, latencia end-to-end (`kminion_end_to_end_*`). |
| NATS *(pendiente)* | `natsio/prometheus-nats-exporter`     | `nats-exporter:7777/metrics`  | `varz`, `connz`, `jsz` (JetStream): conexiones, mensajes, streams, consumers. |

### Visualización en Grafana

- Datasource Prometheus provisionado automáticamente en
  [grafana/provisioning/datasources/datasources.yml](./grafana/provisioning/datasources/datasources.yml).
- Para dashboards prefabricados de Grafana.com (p. ej. kminion id `14012`):
  *Dashboards → Import → ID*.

### Añadir un broker nuevo al scrape

1. Su exporter debe estar en la red `messaging-net` (es el caso si el broker
   se levanta con su propio `docker-compose.yml` del playground).
2. Añadir un bloque en `prometheus.yml`:
   ```yaml
   - job_name: <nombre>
     static_configs:
       - targets: ["<servicio-exporter>:<puerto-interno>"]
   ```
3. Recargar: `docker compose restart prometheus`.

---

## 2. Logs — pipeline push (Fluent Bit → OpenSearch)

```
   [contenedores Docker]                  [fluent-bit]                [opensearch]              [dashboards]
   docker logging driver "json-file"
   /var/lib/docker/containers/<id>/<id>-json.log
            │                                  │                            │                       │
            └─── tail input ───────────────────┤                            │                       │
                                               ├── parser (json) ───────────┤                       │
                                               └── output: opensearch ──────► index docker-logs-*  ──► Discover / dashboards
```

- **Sin instrumentar nada en el broker**: Docker escribe los logs de cada
  contenedor en `/var/lib/docker/containers/<id>/<id>-json.log`. Fluent Bit
  monta ese directorio como solo-lectura y los procesa con el plugin `tail`.
- Cada línea se parsea como JSON (campos `log`, `stream`, `time`) y se envía
  al output `opensearch`. El plugin crea un índice por día con el patrón
  `docker-logs-YYYY.MM.DD` (Logstash-style), lo que permite políticas de
  retención por edad.
- Configuración:
  - [fluent-bit/fluent-bit.conf](./fluent-bit/fluent-bit.conf) — pipeline.
  - [fluent-bit/parsers.conf](./fluent-bit/parsers.conf) — parsers JSON.

### Visualización en OpenSearch Dashboards

1. Abrir <http://localhost:5601>.
2. *Stack Management → Index Patterns → Create*.
3. Patrón: `docker-logs-*`, campo de tiempo: `@timestamp`.
4. Ir a *Discover* y filtrar por `kubernetes.container_name` /
   `log` / lo que necesites.

### Visualización en Grafana

Datasource `OpenSearch` también provisionado, por si se prefiere construir
dashboards mixtos métricas + logs en Grafana usando el plugin
`grafana-opensearch-datasource`.

### Requisitos para que los logs de un broker se recojan

- **Nada en el broker**: el driver de logging por defecto de Docker
  (`json-file`) es suficiente. No hace falta sidecar ni librería.
- Si un contenedor usa un driver distinto (`none`, `syslog`, etc.) sus logs
  no aparecerán en `/var/lib/docker/containers/*` y Fluent Bit no podrá
  leerlos. Por defecto Docker Desktop ya usa `json-file`.

---

## Arranque

```bash
docker network create messaging-net          # solo la primera vez
docker compose up -d
```

Apagado: `docker compose down` (con `-v` para borrar índices y TSDB).

## Accesos rápidos

- Prometheus:           <http://localhost:9090>
- Grafana:              <http://localhost:3000>  (`admin` / `admin`)
- OpenSearch (API):     <http://localhost:9200>
- OpenSearch Dashboards: <http://localhost:5601>
