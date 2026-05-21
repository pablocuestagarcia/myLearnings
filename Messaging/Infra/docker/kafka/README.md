# Kafka — Stack local

Apache Kafka en modo **KRaft** (sin Zookeeper) usando la distribución
**Confluent Community** y una UI de gestión.

## Servicios

| Servicio   | Imagen                                              | Puerto host    | Rol |
| ---------- | --------------------------------------------------- | -------------- | --- |
| `kafka`    | `confluentinc/cp-kafka:7.7.1`                       | `9092`, `9094` | Broker (combina controller + broker en KRaft). |
| `console`  | `docker.redpanda.com/redpandadata/console:v2.7.2`   | `8080`         | UI web para administrar topics, consumers y schemas. |
| `kminion`  | `docker.redpanda.com/redpandadata/kminion:v2.2.12`  | `8081`         | Exporter de métricas Kafka para Prometheus. |

## Imágenes y por qué estas

- **Broker → `confluentinc/cp-kafka`**: distribución mantenida por Confluent,
  el proveedor de referencia del ecosistema Kafka. Es la imagen estándar
  usada en documentación oficial, formación y producción.
- **UI → Redpanda Console**: proyecto OSS mantenido por Redpanda Data,
  compatible con Kafka estándar. Sustituye a Provectus Kafka UI (archivado
  en 2024) como opción de facto actual.
- **Exporter → kminion**: exporter Prometheus mantenido por Redpanda Data.
  Frente a `kafka-exporter` (mantenimiento irregular), kminion ofrece
  métricas de consumer lag, topics, brokers y end-to-end latency, y se
  actualiza con regularidad.

## Listeners

```
  HOST (tu Mac)                Docker network: messaging-net
  ─────────────                ─────────────────────────────
  localhost:9094  ──EXTERNAL──►   kafka:9094
                                  kafka:9092  ◄──PLAINTEXT── otros contenedores
                                  kafka:9093  (CONTROLLER, interno)
```

- Desde **tu host** (CLI local, apps no dockerizadas): `localhost:9094`.
- Desde **otro contenedor en `messaging-net`**: `kafka:9092`.

## Requisitos

```bash
docker network create messaging-net          # solo la primera vez
cd ../observability && docker compose up -d  # plano de métricas/logs
```

## Levantar

```bash
docker compose up -d
docker compose ps
docker compose logs -f kafka
```

Apagado: `docker compose down` (con `-v` para borrar el volumen del broker).

## Acceso

- Redpanda Console (UI): <http://localhost:8080>
- Métricas kminion (texto plano Prometheus): <http://localhost:8081/metrics>

## Smoke tests

```bash
# Crear un topic
docker exec -it kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create --topic demo --partitions 3 --replication-factor 1

# Listar topics
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Producir
docker exec -it kafka kafka-console-producer \
  --bootstrap-server localhost:9092 --topic demo

# Consumir
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 --topic demo --from-beginning
```

## Métricas que verás en Prometheus

kminion expone, entre otras:

- `kafka_topic_partitions`, `kafka_topic_partition_high_water_mark`
- `kafka_consumergroup_group_lag` (lag por grupo y por topic/partición)
- `kafka_broker_info`, `kafka_cluster_info`
- `kminion_end_to_end_*` (latencia end-to-end medida produciendo/consumiendo
  un topic interno; útil para comparar rendimiento entre tecnologías).

El scrape lo realiza el Prometheus del stack de observabilidad
([../observability/prometheus/prometheus.yml](../observability/prometheus/prometheus.yml)).
