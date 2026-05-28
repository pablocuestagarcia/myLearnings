# Laboratorio: Autoscaling en Kubernetes con kind, NATS y KEDA

Este laboratorio cubre los tres mecanismos de autoscaling que se pueden probar de forma realista en un clúster local creado con kind:

1. **HPA** (Horizontal Pod Autoscaler) — escalado por métricas de recursos (CPU/memoria).
2. **VPA** (Vertical Pod Autoscaler) — ajuste automático de `requests`/`limits`.
3. **KEDA + NATS JetStream** — escalado event-driven por longitud de cola.

Karpenter y Cluster Autoscaler quedan **fuera del laboratorio** porque dependen de un cloud provider real y no pueden ejecutarse contra los nodos-contenedor de kind.

---

## 1. Introducción teórica

### 1.1. HPA — Horizontal Pod Autoscaler

HPA es un recurso nativo (`autoscaling/v2`) que cambia el número de réplicas de un `Deployment`, `StatefulSet` o `ReplicaSet` en respuesta a métricas observadas. El controlador vive dentro del `kube-controller-manager`, consulta las métricas cada 15 segundos (configurable con `--horizontal-pod-autoscaler-sync-period`) y aplica la fórmula:

```
desiredReplicas = ceil( currentReplicas × (currentMetric / targetMetric) )
```

Las métricas se obtienen de tres APIs distintas:

- `metrics.k8s.io` — servida por **metrics-server**, da CPU y memoria por pod.
- `custom.metrics.k8s.io` — servida por un adaptador (por ejemplo `prometheus-adapter`), expone métricas de aplicación.
- `external.metrics.k8s.io` — métricas que no provienen de un objeto Kubernetes (longitud de una cola SQS, mensajes en Kafka, etc.). **Esta API es la que utiliza KEDA**.

Para que HPA funcione es **imprescindible que los pods declaren `resources.requests`** en CPU/memoria, porque la "utilización" se calcula como `uso real / request`. Sin requests, el HPA no tiene denominador y no puede decidir.

Tiene mecanismos para evitar oscilaciones (*flapping*): el `behavior.scaleDown.stabilizationWindowSeconds` (por defecto 300s) hace que las reducciones de réplicas se posterguen hasta que la métrica se haya estabilizado.

### 1.2. VPA — Vertical Pod Autoscaler

VPA **no es nativo** de Kubernetes: se instala como un componente aparte del proyecto `kubernetes/autoscaler`. Su trabajo es ajustar los `requests` y `limits` de los contenedores basándose en el uso histórico.

Tiene tres piezas:

- **Recommender** — observa métricas (de metrics-server o Prometheus) y mantiene una recomendación por contenedor. Calcula percentiles del uso histórico (P90 para "target", P95 para "upperBound", P50 para "lowerBound").
- **Updater** — detecta pods cuyos requests están lejos de la recomendación y los desaloja para que el scheduler los recree con los nuevos valores.
- **Admission Controller** — un mutating webhook que reescribe los `requests`/`limits` en el momento de la creación del pod, usando la recomendación más reciente.

Modos de operación (`updatePolicy.updateMode`):

- `Off` — solo genera recomendaciones, no toca pods. **Es el modo más útil para descubrir si tus requests están bien dimensionados.**
- `Initial` — aplica recomendaciones solo al crear el pod.
- `Recreate` / `Auto` — desaloja y recrea pods activamente.
- `InPlaceOrRecreate` — en Kubernetes ≥1.27 intenta redimensionar in-place sin recrear el pod.

⚠️ **No combines HPA y VPA sobre la misma métrica** (CPU o memoria): entran en bucle. Las combinaciones sanas son HPA por métrica custom + VPA dimensionando recursos, o VPA en `Off` como herramienta de capacity planning junto a HPA.

### 1.3. KEDA — Kubernetes Event-Driven Autoscaling

KEDA es un proyecto CNCF que **extiende** HPA para escalar por métricas externas y eventos. Aporta dos cosas que HPA por sí solo no hace:

- **Escalado a cero**: HPA tiene un `minReplicas: 1` como mínimo efectivo (no escala a 0). KEDA sí lo hace, activando un pod cuando aparece trabajo.
- **Conectores ("scalers") a más de 60 sistemas**: Kafka, RabbitMQ, **NATS JetStream**, Redis, PostgreSQL, Prometheus, AWS SQS, Azure Service Bus, etc.

Arquitectura (ver §2.2):

- **Operator** — observa los CRDs `ScaledObject`/`ScaledJob`, crea HPAs detrás del telón y maneja la activación/desactivación.
- **Metrics Adapter** — implementa la API `external.metrics.k8s.io`. Cuando el HPA pregunta "¿cuántos mensajes hay en la cola?", el adapter consulta al scaler y responde.

El CRD principal es `ScaledObject`, que apunta a un `Deployment` y declara uno o más `triggers` (cada trigger es un scaler con su configuración).

### 1.4. NATS y NATS JetStream

NATS es un sistema de mensajería ligero, escrito en Go, originalmente pub/sub at-most-once. **JetStream** es la capa de persistencia y entrega garantizada añadida en 2020; convierte NATS en un broker con streams persistentes, consumers durables y semánticas at-least-once / exactly-once.

Conceptos clave:

- **Subject** — el "topic" en NATS (jerárquico con `.`, soporta wildcards: `orders.>`).
- **Stream** — almacenamiento persistente de mensajes que caen en uno o varios subjects. Tiene políticas de retención (límites, interés, workqueue), límites por tamaño/edad/mensajes, y almacenamiento en memoria o disco.
- **Consumer** — vista de un stream. Puede ser:
  - **Push** — el servidor entrega mensajes activamente a un subject de delivery.
  - **Pull** — el cliente pide mensajes con `fetch()`. Es el modelo recomendado para workers que escalan.
- **Durable consumer** — sobrevive a reinicios del cliente; el servidor mantiene la posición.

Por qué NATS encaja bien con KEDA: cada consumer expone en el endpoint de monitorización HTTP de NATS (puerto 8222) el número de **mensajes pendientes** (`num_pending`). KEDA consulta ese número y decide cuántas réplicas del worker necesita.

---

## 2. Arquitectura

### 2.1. Bucle de control de HPA

```
┌──────────────┐     pull (cada 15s)    ┌────────────────┐
│ kube-control-│ ─────────────────────► │ metrics.k8s.io │ ◄── metrics-server
│ ler-manager  │                        └────────────────┘
│  (HPA loop)  │                                ▲
│              │                                │ kubelet /metrics/resource
│              │                                │
└──────┬───────┘
       │ scale (replicas)
       ▼
┌──────────────┐
│  Deployment  │ ──► ReplicaSet ──► Pods
└──────────────┘
```

El HPA calcula `desiredReplicas` y actualiza el campo `spec.replicas` del target. El ReplicaSet controller hace el resto.

### 2.2. Arquitectura de KEDA + NATS

```
┌───────────────┐                        ┌──────────────────────┐
│ ScaledObject  │ ◄────── watch ──────── │  KEDA Operator       │
│  (CRD)        │                        │                      │
└───────────────┘                        │  - crea HPA          │
                                         │  - activa pod 0→1    │
                                         └──────────┬───────────┘
                                                    │ creates
                                                    ▼
                                         ┌──────────────────────┐
                                         │  HPA (autogenerated) │
                                         └──────────┬───────────┘
                                                    │ asks for metric
                                                    ▼
                                         ┌──────────────────────┐    HTTP GET
                                         │  KEDA Metrics Adapter│ ─────────────►  NATS :8222
                                         │  (external.metrics)  │                /jsz?consumers=true
                                         └──────────────────────┘
                                                    │ scale
                                                    ▼
                                         ┌──────────────────────┐
                                         │ Consumer Deployment  │ ─── pull ───►   NATS :4222
                                         └──────────────────────┘                 (JetStream)
```

El bucle completo es: el consumer hace `pull` del stream → si va lento, `num_pending` sube en NATS → KEDA lo lee del endpoint de monitorización → el HPA generado pide más réplicas → el operator activa nuevos pods → bajan los mensajes pendientes → KEDA propone bajar réplicas → tras el `cooldownPeriod`, los pods extra se eliminan (incluso a 0 si `minReplicaCount: 0`).

### 2.3. Arquitectura de VPA

```
┌──────────────┐
│ Recommender  │ ── lee uso ─►  metrics-server / Prometheus
└──────┬───────┘
       │ escribe recomendación en el CRD VPA
       ▼
┌──────────────┐
│   VPA (CRD)  │
└──────┬───────┘
       │
       │  ┌─────────────┐
       ├─►│   Updater   │── evict ──► pods cuyas requests están lejos
       │  └─────────────┘
       │
       │  ┌────────────────────┐
       └─►│ Admission Webhook  │── mutating ──► al crear pod, reescribe requests/limits
          └────────────────────┘
```

---

## 3. Laboratorio

### Estructura del repositorio

```
k8s-autoscaling-lab/
├── README.md                    ← este archivo
├── 01-kind/
│   └── kind-config.yaml
├── 02-metrics-server/
│   └── install.sh
├── 03-hpa/
│   ├── deployment.yaml
│   ├── hpa.yaml
│   └── load-generator.yaml
├── 04-vpa/
│   ├── install.sh
│   └── vpa.yaml
└── 05-keda-nats/
    ├── nats-values.yaml
    ├── install-nats.sh
    ├── install-keda.sh
    ├── stream-setup.sh
    ├── consumer.yaml
    ├── producer-job.yaml
    └── scaledobject.yaml
```

### Pre-requisitos

- Docker en marcha
- `kind` ≥ 0.20 ([instalación](https://kind.sigs.k8s.io/docs/user/quick-start/))
- `kubectl` ≥ 1.28
- `helm` ≥ 3.12

### Paso 0 — Crear el cluster

```bash
cd 01-kind
kind create cluster --config kind-config.yaml
kubectl cluster-info --context kind-autoscaling-lab
kubectl get nodes
```

Deberías ver 1 control-plane + 2 workers.

### Paso 1 — Instalar metrics-server

```bash
cd ../02-metrics-server
./install.sh
# Espera a que esté Ready:
kubectl -n kube-system rollout status deployment/metrics-server
kubectl top nodes        # debe responder en ~30s
```

### Paso 2 — Probar HPA

```bash
cd ../03-hpa
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml
kubectl get hpa -w        # deja esta terminal abierta
```

En **otra terminal**, lanza carga:

```bash
kubectl apply -f load-generator.yaml
```

En 1-2 minutos verás que `cpu-demo` pasa de 1 réplica a 3-5. Para detenerlo:

```bash
kubectl delete -f load-generator.yaml
# en ~5 minutos (stabilization window) volverá a 1 réplica
```

### Paso 3 — Probar VPA (modo recomendación)

```bash
cd ../04-vpa
./install.sh              # clona el repo de autoscaler e instala VPA
kubectl apply -f vpa.yaml
# Espera ~5 minutos para que recopile datos del Recommender
kubectl describe vpa cpu-demo-vpa
```

Busca la sección `Recommendation:` — verás `target`, `lowerBound`, `upperBound` calculados a partir del histórico. Compáralos con los requests del Deployment para ver si estás sobre- o infra-aprovisionando.

> 💡 Estamos en `updateMode: Off` para no chocar con HPA. En un caso real, este modo te sirve para hacer **capacity planning**: lo ejecutas una semana, lees las recomendaciones y ajustas los requests a mano.

### Paso 4 — Instalar NATS con JetStream

```bash
cd ../05-keda-nats
./install-nats.sh
kubectl -n nats get pods       # nats-0 debe estar Running
```

### Paso 5 — Instalar KEDA

```bash
./install-keda.sh
kubectl -n keda get pods       # keda-operator y keda-metrics-apiserver Running
```

### Paso 6 — Crear el stream y el consumer en NATS

```bash
./stream-setup.sh
```

Este script lanza un pod efímero (`nats-box`) que se conecta a NATS, crea el stream `ORDERS` con subject `orders.>` y un consumer durable llamado `workers` (modo pull, ack explícito).

### Paso 7 — Desplegar el consumer y configurar el ScaledObject

```bash
kubectl apply -f consumer.yaml          # consumer en Python (a través de ConfigMap)
kubectl apply -f scaledobject.yaml      # ScaledObject de KEDA
kubectl get scaledobject -n nats
kubectl get hpa -n nats                 # KEDA habrá creado uno automáticamente
```

`minReplicaCount: 0`, así que al principio **no hay ningún pod consumer**.

### Paso 8 — Inyectar trabajo y ver el escalado

En **una terminal** observa los pods:

```bash
kubectl get pods -n nats -l app=nats-consumer -w
```

En **otra terminal** lanza el productor:

```bash
kubectl apply -f producer-job.yaml
```

Secuencia esperada:

1. El producer publica 500 mensajes en el subject `orders.new`.
2. `num_pending` del consumer `workers` sube en NATS.
3. KEDA lo detecta (poll cada 5s) y activa el primer pod (0 → 1).
4. Como cada mensaje tarda 2s en procesarse y el `lagThreshold` es 10, KEDA escalará hasta el `maxReplicaCount: 10`.
5. Cuando los pendientes bajen, tras el `cooldownPeriod: 30s` los pods extra se irán retirando.
6. Cuando llegue a 0 pendientes durante el `cooldownPeriod`, **el consumer escala a 0**.

Para inspeccionar en vivo lo que ve KEDA:

```bash
kubectl -n nats port-forward svc/nats 8222:8222
# en otra terminal:
curl -s http://localhost:8222/jsz?consumers=true | jq '.account_details[].stream_detail[].consumer_detail[] | {name, num_pending, num_ack_pending}'
```

### Paso 9 — Limpieza

```bash
kind delete cluster --name autoscaling-lab
```

---

## 4. Ejercicios sugeridos

1. Cambia `lagThreshold` a `1` y observa cómo KEDA se vuelve agresivo (un pod por mensaje).
2. Sustituye el consumer Python por un Deployment con **HPA tradicional** sobre CPU y compara comportamientos. Verás que HPA reacciona tarde porque el trabajo está IO-bound, no CPU-bound — exactamente el caso de uso de KEDA.
3. Ponle un VPA en modo `Off` al consumer y, tras una hora de carga, mira la recomendación. ¿Estás dando demasiada memoria?
4. Desactiva temporalmente NATS (`kubectl -n nats scale sts nats --replicas=0`) y comprueba que el `ScaledObject` entra en estado de error pero el HPA mantiene la última decisión conocida (graceful degradation).

---

## 5. Referencias

- HPA: <https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/>
- VPA: <https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler>
- KEDA: <https://keda.sh/docs/latest/>
- KEDA NATS JetStream scaler: <https://keda.sh/docs/latest/scalers/nats-jetstream/>
- NATS JetStream: <https://docs.nats.io/nats-concepts/jetstream>
- kind: <https://kind.sigs.k8s.io/>
