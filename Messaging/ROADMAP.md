# Messaging Playground — Roadmap

Plan de ejecución por **fases**, cubriendo **dos targets de despliegue**
en paralelo: Docker Compose y Kubernetes (kind). Cada fase tiene su
objetivo, sus entregables por target y un criterio de aceptación.

> Referencias transversales:
> [OVERVIEW.md](./OVERVIEW.md) ·
> [Infra/README.md](./Infra/README.md).

## Leyenda de estado

| Símbolo | Significado |
| ------- | ----------- |
| `[x]`   | Hecho       |
| `[~]`   | En curso    |
| `[ ]`   | Pendiente   |

## Convenciones sobre targets

- **D** → entregable en **Docker Compose** ([Infra/docker/](./Infra/docker/)).
- **K** → entregable en **Kubernetes** ([Infra/kubernetes/](./Infra/kubernetes/)).
- Donde una tarea aplica a los dos targets de forma equivalente, se
  indica explícitamente.
- Las **versiones del software** (Kafka, NATS, OpenSearch, …) se
  mantienen alineadas entre targets para que la comparación sea
  honesta.

---

## Fase 0 — Base + observabilidad común

### 0.D — Docker *(hecho)*

- [x] Red Docker compartida `messaging-net`.
- [x] Observabilidad: Prometheus + Grafana + OpenSearch + Fluent Bit.
- [x] Kafka KRaft + Redpanda Console + kminion.
- [x] Documentación.

### 0.K — Kubernetes

- [ ] Cluster `kind` con config en `Infra/kubernetes/cluster/kind-config.yaml`
  (1 control-plane + 2 workers).
- [ ] `ingress-nginx` instalado para exponer servicios al host.
- [ ] Stack `kube-prometheus-stack` en namespace `observability`.
- [ ] `opensearch-operator` + `OpenSearchCluster` (1 nodo, dev).
- [ ] `fluent/fluent-bit` Helm chart como DaemonSet, con filtro `kubernetes`.
- [ ] Strimzi operator en namespace `kafka`; `Kafka` CR mínimo (1 broker
  KRaft) + `KafkaNodePool`.
- [ ] Redpanda Console (Helm chart) apuntando al `Kafka` de Strimzi.

**Aceptación (común)**: tras arrancar el target desde cero, ver métricas
de Kafka en Grafana y logs en OpenSearch Dashboards.

---

## Fase 1 — Kafka: pista de desarrollador

Aplica a los dos targets. La diferencia está en *cómo* se añaden los
componentes (servicio en compose vs. CRDs/Helm).

### 1.1 Schema Registry y serialización

- [ ] **D**: `confluentinc/cp-schema-registry` en el stack Kafka.
- [ ] **K**: Schema Registry vía chart (`confluentinc/cp-schema-registry`
  en su Helm chart oficial o `bitnami/schema-registry` revisando licencia).
- [ ] App productora/consumidora en Python (`confluent-kafka`) y/o Java
  publicando el mismo mensaje en **Avro**, **Protobuf** y **JSON Schema**.
- [ ] Probar compatibilidad `BACKWARD`, `FORWARD` y `FULL` rompiendo el
  schema a propósito.
- [ ] Integrar Redpanda Console con el Schema Registry para inspección.

**Aceptación**: producir con schema v1, evolucionar a v2 (`BACKWARD`) y
consumir con la app v1 sin redeploy, en ambos targets.

### 1.2 Kafka Connect

- [ ] **D**: `confluentinc/cp-kafka-connect` en modo distribuido.
- [ ] **K**: Strimzi `KafkaConnect` CR + `KafkaConnector` CRs (declarativo).
- [ ] Demo *source*: JDBC Source desde un Postgres → topic.
- [ ] Demo *sink*: Topic → MinIO (S3 local).
- [ ] SMTs (`InsertField`, `MaskField`).

**Aceptación**: el `KafkaConnector` declarativo en k8s reproduce el mismo
pipeline que se montó a mano en compose.

### 1.3 ksqlDB

- [ ] **D**: `confluentinc/cp-ksqldb-server` + `cp-ksqldb-cli`.
- [ ] **K**: ksqlDB vía su Helm chart oficial.
- [ ] Stream + tabla, join stream-table, agregado con `TUMBLING`,
  pull query desde la CLI.

### 1.4 Kafka Streams (Java)

- [ ] **Común**: app Java en `Messaging/apps/streams-demo/` con
  topología, estado local (RocksDB) y *exactly-once*.
- [ ] **D**: ejecutar la app como contenedor en `messaging-net`.
- [ ] **K**: desplegar como `Deployment` (con `affinity` para co-localizar
  con brokers no es necesario aquí).

**Aceptación**: matar el contenedor / borrar el pod mientras procesa y,
al volver, no duplica ni pierde mensajes.

### 1.5 Transacciones y patrones avanzados

- [ ] Productor transaccional + consumidor `read_committed`.
- [ ] **Patrón DLQ** con retry topics.
- [ ] **Outbox pattern** con Debezium (Postgres → Kafka).
  - **D**: imagen `debezium/connect` como servicio.
  - **K**: Strimzi `KafkaConnect` con el conector Debezium.

---

## Fase 2 — Kafka: pista de plataforma (básico)

Aquí la diferencia entre targets es **grande**: en k8s muchas operaciones
las hace el operator, en Docker hay que ejecutarlas a mano. Eso es parte
del aprendizaje.

### 2.1 Almacenamiento y retención

- [ ] **Común**: topics con `cleanup.policy=delete` y otros con `compact`.
- [ ] **D**: modificar `log.segment.bytes` y `log.retention.ms` vía
  variables del compose; observar el filesystem del volumen `kafka_data`.
- [ ] **K**: configurarlo vía `KafkaTopic` CRs y `Kafka.spec.kafka.config`;
  inspeccionar los PVCs.
- [ ] Generar tombstones y verificar compactación en los dos targets.

### 2.2 Particionado y reasignación

- [ ] **D**: compose alternativo `kafka-cluster/` con 3 brokers KRaft;
  reasignación manual con `kafka-reassign-partitions`.
- [ ] **K**: aumentar `KafkaNodePool.spec.replicas` a 3; usar la Cruise
  Control integrada en Strimzi para balanceo automático.
- [ ] Drill de *preferred leader election* tras simular caída.

### 2.3 Listeners y conexiones

- [ ] **D**: documentar el efecto de `advertised.listeners` con cliente
  local vs cliente en contenedor.
- [ ] **K**: configurar `Kafka.spec.kafka.listeners` (internal + external
  vía `Ingress`/`NodePort`/`LoadBalancer`); validar conexión desde fuera
  del cluster con el certificado adecuado.

### 2.4 Cuotas y multi-tenancy

- [ ] **D**: `kafka-configs --entity-type clients` con `producer_byte_rate`.
- [ ] **K**: cuotas declarativas vía `KafkaUser.spec.quotas`.
- [ ] Cliente "ruidoso" vs "bien comportado"; observar el throttling
  en métricas.

### 2.5 Mantenimiento operacional

- [ ] **D**: rolling restart manual (`docker compose restart kafka-1 …`).
- [ ] **K**: rolling update automático cambiando la versión en el `Kafka`
  CR; observar la *rolling restart annotation* y la garantía de quorum.
- [ ] Subir versión Kafka (minor → minor): cambio de tag (D) vs
  actualización del CR + `inter.broker.protocol.version` (K).

---

## Fase 3 — Pruebas de rendimiento

Independientes del target salvo por dónde se ejecutan. Generan **una
línea base** que servirá para medir el coste de TLS, replicación, etc.

### 3.1 Herramientas

- [ ] Carpeta `Messaging/perf/` con scripts reproducibles.
- [ ] **Kafka**: `kafka-producer-perf-test`, `kafka-consumer-perf-test`
  (disponibles en `cp-kafka`).
- [ ] **NATS** (cuando exista el stack): `nats bench`.
- [ ] Cargas: throughput sostenido, *burst*, mensajes pequeños (256 B) y
  grandes (64 KB).

### 3.2 Variables a explorar

- [ ] `acks` ∈ {`0`, `1`, `all`}.
- [ ] `linger.ms`, `batch.size`.
- [ ] `compression.type` ∈ {`none`, `lz4`, `zstd`, `snappy`}.
- [ ] Particiones (1, 3, 12).
- [ ] Tamaño de mensaje y nº de productores concurrentes.

### 3.3 Métricas

- [ ] Throughput (msg/s, MB/s) productor y consumidor.
- [ ] Latencia: media, p95, p99.
- [ ] `kminion_end_to_end_*` (D) / equivalentes de Strimzi (K).
- [ ] Consumer lag durante *burst*.
- [ ] CPU/RAM (D: `docker stats` o `cadvisor`; K: `kube-state-metrics` y
  `node-exporter` ya incluidos en `kube-prometheus-stack`).

### 3.4 Entregables

- [ ] Dashboard "Kafka — perf baseline" en Grafana (mismo JSON para los
  dos targets).
- [ ] `perf/results.md` con números por combinación de parámetros,
  separados por target.
- [ ] Mismo formato preparado para NATS, para comparar 1-a-1.

**Aceptación**: ejecutar un script y, sin tocar el dashboard, ver los
percentiles del último run en cualquiera de los dos targets.

---

## Fase 4 — NATS: paridad con Kafka

### 4.D — Docker

- [ ] Stack `Infra/docker/nats/` con `nats:2.10` + JetStream.
- [ ] `natsio/prometheus-nats-exporter` + `job` en Prometheus.
- [ ] UI: `nats-box` (CLI oficial) en el compose para gestionar streams.

### 4.K — Kubernetes

- [ ] Helm chart oficial `nats-io/nats` con JetStream activado.
- [ ] `ServiceMonitor` para el exporter (incluido en el chart con
  `metrics.enabled=true`).

### Común

- [ ] Apps cliente equivalentes a las de Kafka (mismo caso de uso).
- [ ] Repetir los benchmarks de la fase 3 con `nats bench`.
- [ ] `perf/comparison.md` con tabla y dashboards Grafana lado a lado.

---

## Fase 5 — Seguridad

A partir de aquí, **la mayoría de tareas avanzan más rápido en K** porque
los operators ya integran TLS, SASL y rotación. En D se hacen *a pelo*
para entender qué está pasando por debajo.

### 5.1 Certificados (CA local)

- [ ] `Infra/security/ca/` con script para generar CA + certificados
  (cfssl u openssl). Reutilizable por los dos targets.

### 5.2 TLS y mTLS

- [ ] **D · Kafka**: listener `SSL://` con keystore/truststore JKS;
  variante mTLS (`ssl.client.auth=required`).
- [ ] **K · Kafka**: `Kafka.spec.kafka.listeners[].tls=true` y
  `authentication.type=tls`; Strimzi gestiona los certificados y su
  rotación.
- [ ] **D · NATS**: TLS en `4222`/`8222`; mTLS para JetStream.
- [ ] **K · NATS**: valores del chart con `tls.enabled=true` y secret
  con la CA.
- [ ] **D · OpenSearch**: re-habilitar el plugin `security` (la base lo
  desactiva).
- [ ] **K · OpenSearch**: el operator gestiona la `security` config
  automáticamente.
- [ ] **D · Grafana**: TLS en `:3000`, datasources HTTPS.
- [ ] **K · Grafana**: TLS termina en `Ingress` (`cert-manager` + Let's
  Encrypt staging para practicar, o CA local).
- [ ] **D/K · Prometheus**: scrape con `scheme: https` y `tls_config`.

### 5.3 Autenticación

- [ ] **Kafka**: SASL/SCRAM-SHA-512 (usuarios `app-producer`,
  `app-consumer`, `admin`).
  - **D**: `kafka-configs` para crear usuarios.
  - **K**: `KafkaUser.spec.authentication.type=scram-sha-512`.
- [ ] **NATS**: cuentas y usuarios con permisos por subject.
- [ ] **OpenSearch**: roles internos para Grafana y Fluent Bit con
  least-privilege en `*-logs-*`.
- [ ] **Grafana**: integrar con Keycloak (OIDC) en lugar de `admin/admin`.

### 5.4 Autorización

- [ ] **Kafka**: ACLs.
  - **D**: `kafka-acls` por `client.id`.
  - **K**: `KafkaUser.spec.authorization.acls` (declarativo).
- [ ] **NATS**: permisos por subject por cuenta.
- [ ] Tests automatizados de negación explícita.

**Aceptación**: regenerar la CA y los secretos desde el script, arrancar
el stack completo cifrado en los dos targets, sin intervención manual.

---

## Fase 6 — Alta disponibilidad y réplicas

### 6.1 Kafka

- [ ] **D**: compose `kafka-cluster/` con 3 brokers KRaft + `min.insync.
  replicas=2` y `replication.factor=3`.
- [ ] **K**: `KafkaNodePool.spec.replicas=3` con `antiAffinity` para
  distribuir entre nodos del cluster kind.
- [ ] Drill: tirar un broker bajo carga, verificar 0 pérdida con
  `acks=all`.

### 6.2 NATS

- [ ] **D**: cluster NATS de 3 nodos (3 servicios en el compose).
- [ ] **K**: chart con `replicaCount=3` y `jetstream.replicas=3`.
- [ ] Streams JetStream con `R=3`; drill equivalente al de Kafka.

### 6.3 OpenSearch

- [ ] **D**: 3 servicios opensearch en el compose, `discovery.seed_hosts`
  mutuo.
- [ ] **K**: `OpenSearchCluster` con 3 *data nodes*.
- [ ] Índices `*-logs-*` con `number_of_replicas=1`.

### 6.4 Prometheus y Grafana

- [ ] **K**: HA real con dos Prometheus replicados (Thanos / Mimir como
  ejercicio aparte si el alcance crece demasiado).
- [ ] **K**: Grafana con BD externa (Postgres) y `replicas=2`.

**Aceptación**: cada cluster sobrevive a la caída de un nodo sin pérdida
de datos ni interrupciones visibles en Grafana.

---

## Fase 7 — Backups y disaster recovery

### 7.1 Kafka

- [ ] **D**: MirrorMaker 2 entre dos clusters Kafka en el mismo compose.
- [ ] **K**: `KafkaMirrorMaker2` CR de Strimzi entre dos clusters Kafka
  del mismo cluster k8s.
- [ ] Simular pérdida total del primario y validar *failover*.

### 7.2 NATS

- [ ] Mirroring de streams JetStream a un segundo cluster NATS.
- [ ] Snapshots a MinIO.

### 7.3 OpenSearch

- [ ] Snapshots periódicos a MinIO (plugin `repository-s3`).
- [ ] Script de restore en un cluster vacío.

### 7.4 Prometheus

- [ ] Snapshots de TSDB (`/api/v1/admin/tsdb/snapshot`) a MinIO.
- [ ] Alternativa: `remote_write` a un backend persistente
  (VictoriaMetrics/Mimir/Thanos).

**Aceptación**: tras `down -v` (D) o borrar el namespace (K), restaurar
desde backup deja el sistema en el estado previo.

---

## Fase 8 — Gestión de secretos

Hasta esta fase, los secretos viven en `environment:` (D) o `Secret`
manuales (K), lo cual no es aceptable para producción.

- [ ] **D**: HashiCorp Vault en `Infra/secrets/` (imagen oficial
  `hashicorp/vault`), motor KV v2 y políticas por servicio. Integración
  vía `vault-agent` sidecar o `envconsul`.
- [ ] **K**: Vault con `vault-helm` chart oficial +
  `external-secrets-operator` para sincronizar `Secret` desde Vault.
- [ ] Alternativa ligera (en los dos): **sops** + age para encriptar
  archivos `.env`/`Secret` en el repo.
- [ ] Documentar rotación de un secreto end-to-end.

**Aceptación**: ningún manifiesto del repo contiene contraseñas o keys
en claro.

---

## Fase 9 — Hardening final y SLOs

- [ ] **D**: límites de CPU/memoria por servicio (`deploy.resources`).
- [ ] **K**: `resources.requests/limits`, `NetworkPolicy` entre
  namespaces, `PodSecurityStandards`.
- [ ] **K**: separación de redes vía `NetworkPolicy`
  (`data` ↔ `control` ↔ `observability`) — equivalente a las múltiples
  redes Docker en D.
- [ ] Audit logs en Kafka, NATS y OpenSearch enviados al pipeline.
- [ ] **SLIs/SLOs**:
  - Kafka: consumer lag bajo umbral, latencia end-to-end p95.
  - NATS: ack latency, mensajes pendientes en JetStream.
  - OpenSearch: query latency, *cluster status*.
- [ ] Reglas de alerta en Prometheus y panel de SLO en Grafana.
- [ ] **K**: `PrometheusRule` CR para que las reglas viajen con el chart.

**Aceptación**: una violación deliberada de cada SLO dispara la alerta
correspondiente.

---

## Orden de prioridad sugerido

1. **Cerrar fase 0.K** (paridad de base entre targets) antes de avanzar.
   Sin esto, las fases siguientes solo crecen en un lado.
2. **Fase 1.1** (Schema Registry) en los dos targets — desbloquea
   Connect, ksqlDB e inspección con Console.
3. **Fase 3** (rendimiento) cuanto antes, sobre lo que haya. Da línea
   base para medir el coste de cada fase siguiente.
4. **Fase 4** (NATS) antes de invertir en seguridad/HA: la comparativa
   honra la simplicidad inicial.
5. **Fases 5–8** en orden: TLS primero (habilita réplicas seguras), luego
   réplicas, luego backups (que necesitan datos que valga la pena
   guardar), por último secretos bien gestionados.
6. **Fase 9** como cierre, cuando el stack es estable y comparable.
