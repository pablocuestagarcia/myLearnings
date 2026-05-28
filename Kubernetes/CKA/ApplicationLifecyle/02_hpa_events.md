# Análisis de Eventos HPA en Kubernetes
## Causa Raíz, Diagnóstico y Operación Diaria

---

## PARTE 1: EVENTOS ESPECIFICADOS

### Pregunta 1: ¿Cuál es la causa del evento `FailedGetResourceMetric` en el HPA de nginx-deployment?

#### Análisis Teórico

El evento **`FailedGetResourceMetric`** es un indicador crítico que refleja la **incapacidad del HPA Controller para obtener métricas de recursos (CPU o Memoria)** necesarias para calcular la cantidad de réplicas requeridas.

**Arquitectura subyacente:**

```
┌─────────────────────────────────────────────────────────┐
│                  HPA Controller                         │
│  (autoscaling.k8s.io v2)                               │
└──────────────────┬──────────────────────────────────────┘
                   │ Consulta cada 15 segundos (por defecto)
                   │ GET /apis/metrics.k8s.io/v1beta1/...
                   ▼
┌─────────────────────────────────────────────────────────┐
│           Metrics Server                                │
│  (kubernetes-sigs/metrics-server)                       │
│  - Recopila datos de kubelet cada 15s                   │
│  - Calcula promedios                                    │
│  - Expone API REST                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           Kubelet (en cada nodo)                        │
│  - cgroup stats (CPU, Memory)                           │
│  - Container runtime metrics                            │
└─────────────────────────────────────────────────────────┘
```

**Si `FailedGetResourceMetric` ocurre, significa que en algún punto de esta cadena falló la comunicación.**

#### Causas Raíz Principales

| # | Causa | Síntoma | Diagnóstico |
|---|-------|---------|------------|
| **1** | Metrics Server no está instalado | HPA siempre muestra "unknown" | `kubectl get deployment -n kube-system metrics-server` |
| **2** | Metrics Server en CrashLoop | API de métricas no disponible | `kubectl logs -n kube-system -l k8s-app=metrics-server` |
| **3** | Pod sin `requests` definidos | Métricas no se pueden calcular en % | `kubectl get pod -o yaml \| grep -A5 resources` |
| **4** | Kubelet no reporta métricas | Datos no llegan a Metrics Server | `kubectl debug node/<nodename>` |
| **5** | Pod en estado Pending | No hay CPU/Memory data aún | `kubectl get pods -o wide` |
| **6** | Network policy bloqueando | HPA no puede contactar API | `kubectl get networkpolicy -A` |

#### Causa Raíz #1: Metrics Server No Instalado

```bash
# Verificar si existe
kubectl get deployment -n kube-system metrics-server

# Si no existe, instalar
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verificar estado
kubectl get deployment metrics-server -n kube-system
kubectl logs -n kube-system -l k8s-app=metrics-server
```

**Evento que se observaría:**

```bash
$ kubectl describe hpa nginx-hpa

Events:
  Type     Reason                   Age   From                       Message
  ----     ------                   ---   ----                       -------
  Warning  FailedGetResourceMetric  2m    horizontal-pod-autoscaler  
           unable to get metrics for cpu: no metrics returned from resource metrics API
```

#### Causa Raíz #3: Pod Sin Requests Definidos

**Concepto fundamental**: El HPA calcula **utilización porcentual**, que matemáticamente es:

```
Utilización (%) = (Uso Real / Requests) × 100
```

**Si no hay `requests` definidos**, no hay denominador, por lo tanto no se puede calcular %.

```yaml
# ❌ INCORRECTO - Causará FailedGetResourceMetric
apiVersion: v1
kind: Pod
metadata:
  name: nginx-bad
spec:
  containers:
  - name: nginx
    image: nginx:latest
    # ← Sin resources/requests

---
# ✅ CORRECTO
apiVersion: v1
kind: Pod
metadata:
  name: nginx-good
spec:
  containers:
  - name: nginx
    image: nginx:latest
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

**Diagnóstico:**

```bash
# Ver si el deployment tiene requests
kubectl get deployment nginx-deployment -o json | \
  jq '.spec.template.spec.containers[].resources.requests'

# Salida correcta:
# {
#   "cpu": "100m",
#   "memory": "128Mi"
# }

# Salida incorrecta (null o empty object):
# null
```

#### Causa Raíz #4: Latencia en Recopilación de Métricas

**Teoría**: Metrics Server necesita ~1-2 ciclos de recopilación para tener datos suficientes.

- **Ciclo 1** (0-15s): Recopila baseline
- **Ciclo 2** (15-30s): Calcula promedios
- **Ciclo 3+** (>30s): HPA puede actuar

```
TIMELINE:
─────────────────────────────────────────────
T=0s    Pod inicia
T=15s   Metrics Server recoge 1era métrica
T=30s   Metrics Server calcula promedio
T=45s   HPA puede ver métricas ✓
─────────────────────────────────────────────
```

**Solución**: Esperar 1-2 minutos después de crear deployment

```bash
kubectl apply -f deployment.yaml
sleep 120  # Esperar que métricas se estabilicen
kubectl get hpa -w
```

#### Solución Integral para nginx-deployment

```bash
# PASO 1: Verificar que Metrics Server existe
kubectl get deployment -n kube-system metrics-server
# Si no, instalar:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# PASO 2: Verificar que nginx-deployment tiene requests
kubectl get deployment nginx-deployment -o yaml | grep -A10 "resources:"

# PASO 3: Si no tiene, agregar
kubectl set resources deployment nginx-deployment \
  --requests=cpu=100m,memory=128Mi \
  --limits=cpu=500m,memory=512Mi

# PASO 4: Esperar y validar
sleep 120
kubectl get hpa -w
kubectl describe hpa nginx-hpa

# PASO 5: Verificar en Metrics API directamente
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods" | jq .
```

**Evento esperado después de fix:**

```bash
Events:
  Type    Reason             Age   From                       Message
  ----    ------             ---   ----                       -------
  Normal  SuccessfulRescale  30s   horizontal-pod-autoscaler  
          New size: 2; reason: cpu resource utilization (percentage of request: 45%);
```

---

### Pregunta 2: ¿Qué indica el evento `ScalingReplicaSet` en el HPA de nginx-deployment?

#### Análisis Teórico

El evento **`ScalingReplicaSet`** es un indicador de **acción exitosa de escalado**. Refleja que:

1. El HPA Controller **calculó correctamente** el número deseado de réplicas
2. **Modificó exitosamente** el ReplicaSet subyacente
3. El **cambio está en progreso** o completado

**Arquitectura conceptual:**

```
┌──────────────────────────────────┐
│    Deployment                    │
│  nginx-deployment                │
└──────────────────────────────────┘
         │ Controls
         ▼
┌──────────────────────────────────┐
│    ReplicaSet                    │
│  nginx-deployment-5d4ph          │
│  spec.replicas: 3 → 5            │
└──────────────────────────────────┘
         │ Creates
         ▼
┌──────────────────────────────────┐
│         Pods                     │
│  nginx-deployment-5d4ph-xxxxx    │
│  nginx-deployment-5d4ph-yyyyy    │
│  nginx-deployment-5d4ph-zzzzz    │
└──────────────────────────────────┘
```

**El evento `ScalingReplicaSet` ocurre en el nivel de ReplicaSet**, no en el Deployment.

#### Interpretación del Evento

```bash
$ kubectl describe hpa nginx-hpa

Events:
  Type    Reason                   Age    From                       Message
  ----    ------                   ----   ----                       -------
  Normal  SuccessfulRescale        2m30s  horizontal-pod-autoscaler  
          New size: 5; reason: cpu resource utilization 
          (percentage of request: 85%); 
          new size: 5
```

**Desglose del evento:**

| Campo | Significado |
|-------|------------|
| `Type: Normal` | Escalado se completó sin errores |
| `Reason: SuccessfulRescale` | HPA logró cambiar replicas |
| `New size: 5` | Ahora hay 5 pods (antes había 3) |
| `percentage of request: 85%` | Métrica que disparó: CPU al 85% |

#### Lógica de Cálculo Subyacente

Cuando ves `ScalingReplicaSet`, el HPA ejecutó internamente:

```
1. Obtener métrica actual: CPU promedio = 85%
2. Obtener target: CPU target = 70%
3. Obtener replicas actuales: 3
4. Calcular: 
   desiredReplicas = ceil(
       (85% / 70%) × 3 
   ) = ceil(3.64) = 4
   
5. Aplicar límites:
   Si 4 está entre minReplicas (2) y maxReplicas (10): ✓
   
6. Cambiar: replicas 3 → 4
   → Evento: "ScalingReplicaSet"
   
7. Esperar cooldown: 3 minutos
```

#### Variantes del Evento

**ScalingReplicaSet - Scale Up (Aumento):**

```yaml
Events:
  Type    Reason             Age    Message
  Normal  SuccessfulRescale  10s    New size: 5; reason: cpu resource 
          utilization (percentage of request: 85%)
```

**ScalingReplicaSet - Scale Down (Disminución):**

```yaml
Events:
  Type    Reason             Age    Message
  Normal  SuccessfulRescale  5m     New size: 2; reason: All metrics 
          below target. Reason: cpu resource utilization 
          (percentage of request: 25%)
```

**DidNotScale (Sin cambio):**

```yaml
Events:
  Type    Reason       Age    Message
  Normal  DidNotScale  1m     horizontal-pod-autoscaler  
          the desired replica count is less than the current 
          replica count and one or both of the --horizontal-pod-autoscaler-downscale-stabilization 
          lowerBound is preventing scale-down
```

---

## PARTE 2: EVENTOS SIMILARES DE HPA

### Matriz Completa de Eventos

#### Categoría 1: Eventos de Éxito

```yaml
# EVENT 1: SuccessfulRescale
Reason: "SuccessfulRescale"
Type: Normal
Cuando: HPA cambió exitosamente el número de replicas
Ejemplo:
  New size: 5; reason: cpu resource utilization (percentage of request: 78%)

# EVENT 2: DidNotScale
Reason: "DidNotScale"
Type: Normal
Cuando: Métrica dentro del rango, HPA decide no cambiar replicas
Ejemplo:
  the desired replica count is less than the current replica count and one or both 
  of the --horizontal-pod-autoscaler-downscale-stabilization lower bound is preventing scale-down
```

#### Categoría 2: Eventos de Falla Temporal

```yaml
# EVENT 3: FailedComputeMetricsReplicas
Reason: "FailedComputeMetricsReplicas"
Type: Warning
Cuando: HPA obtuvo métricas pero no puede calcular replicas deseadas
Causas:
  - Métrica corrupta o formato inválido
  - División por cero (no hay requests)
  - Valor NaN o infinito
Ejemplo:
  failed to compute replicas based on cpu resource utilization 
  (percentage of request): missing request for cpu

# EVENT 4: FailedGetResourceMetric (ya explicado arriba)
Reason: "FailedGetResourceMetric"
Type: Warning
Cuando: No se pueden obtener métricas de recursos
Causas:
  - Metrics Server down
  - Pod sin requests
  - Latencia en recopilación

# EVENT 5: FailedGetCustomMetric
Reason: "FailedGetCustomMetric"
Type: Warning
Cuando: No se pueden obtener métricas personalizadas (Prometheus, custom)
Ejemplo:
  failed to get custom metric http_requests_per_second: 
  unable to compute replica count based on custom metric

# EVENT 6: FailedGetExternalMetric
Reason: "FailedGetExternalMetric"
Type: Warning
Cuando: No se pueden obtener métricas externas (cloud provider, etc)
Ejemplo:
  failed to get external metric target-capacity-left: 
  unable to get external metrics API
```

#### Categoría 3: Eventos de Restricción

```yaml
# EVENT 7: TooFewReplicas
Reason: "TooFewReplicas"
Type: Warning
Cuando: Número calculado es menor que minReplicas
Ejemplo:
  the desired replica count 1 is less than the minimum replica count 2

# EVENT 8: TooManyReplicas
Reason: "TooManyReplicas"
Type: Warning
Cuando: Número calculado excede maxReplicas
Ejemplo:
  the desired replica count 150 exceeds the maximum replica count 100

# EVENT 9: InvalidTargetResourceUnitFormat
Reason: "InvalidTargetResourceUnitFormat"
Type: Warning
Cuando: Formato de unidad de métrica es inválido
Ejemplo:
  invalid target resource unit "invalidunit" for metric cpu
```

#### Categoría 4: Eventos de Configuración

```yaml
# EVENT 10: FailedRescale
Reason: "FailedRescale"
Type: Warning
Cuando: HPA intentó cambiar replicas pero falló (RBAC, quota, etc)
Ejemplo:
  failed to rescale deployment nginx-deployment: 
  Forbidden: user cannot update resource "deployments/scale"

# EVENT 11: InvalidSelector
Reason: "InvalidSelector"
Type: Warning
Cuando: scaleTargetRef apunta a recurso inexistente
Ejemplo:
  unable to get target (deployment default/nonexistent): 
  not found
```

---

## PARTE 3: EVENTOS COMUNES EN CKA Y OPERACIÓN DIARIA

### Escenarios del CKA

#### Escenario 1: "Debug del HPA que no escala"

```bash
# PROBLEMA: HPA no escala aunque hay carga
# PASOS DE DIAGNÓSTICO:

Step 1: Ver estado del HPA
kubectl get hpa -A
kubectl describe hpa <name>

Step 2: Revisar eventos
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

Step 3: Identificar el evento
# Si ves: FailedGetResourceMetric
#   → Problema: Metrics, requests, Metrics Server
# Si ves: DidNotScale
#   → Normal: Dentro de rango o en cooldown
# Si ves: FailedComputeMetricsReplicas
#   → Problema: Datos de métrica malformados

Step 4: Resolver según evento
# (Ver tabla de resoluciones abajo)
```

#### Escenario 2: "HPA oscila entre replicas (Flapping)"

```yaml
# PROBLEMA: ReplicaSet cambia constantemente (3→5→3→5...)
# CAUSA: stabilizationWindow muy bajo o target muy agresivo

# SOLUCIÓN:
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: oscillating-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # ← Aumentar a 5 min
      policies:
      - type: Percent
        value: 50      # ← Reducir lentamente
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60   # ← Esperar antes de subir
      policies:
      - type: Percent
        value: 50      # ← Subir moderadamente
        periodSeconds: 30
```

#### Escenario 3: "HPA siempre en maxReplicas"

```bash
# PROBLEMA: HPA alcanzó el límite máximo
# EVENTO OBSERVADO: TooManyReplicas

# Diagnóstico:
kubectl describe hpa <name>
# Ver: "the desired replica count 150 exceeds the maximum replica count 100"

# Opciones de resolución:
# 1. Aumentar maxReplicas (temporal, trata síntoma)
kubectl patch hpa <name> -p '{"spec":{"maxReplicas":200}}'

# 2. Optimizar aplicación (permanente, trata causa)
# - Profiling de CPU/Memory
# - Optimizar algoritmos
# - Cachear resultados
# - Mejorar DB queries

# 3. Escalar nodos (si es problema de recursos en cluster)
kubectl get nodes
kubectl top nodes
```

#### Escenario 4: "Nuevos pods en Pending"

```bash
# PROBLEMA: HPA escaló pero pods no inician
# CAUSA: No hay espacio en nodos (recursos insuficientes)
# EVENTO: FailedRescale o pods en Pending

# Diagnóstico:
kubectl get pods -o wide | grep Pending
kubectl describe pod <pending-pod>
# Ver "Insufficient cpu" o "Insufficient memory"

# Resolución:
# 1. Aumentar nodos (si tienes Cluster Autoscaler)
#    → El CA detectará pods Pending y escalará

# 2. Reducir requests/limits (si están over-sized)
kubectl set resources deployment <name> \
  --requests=cpu=50m,memory=64Mi

# 3. Revisar node capacity
kubectl describe nodes | grep -A5 "Allocated resources"
```

### Tabla de Resolución Rápida

```
┌─────────────────────────────────────┬──────────────────────┬────────────────────┐
│ Evento                              │ Causa Probable       │ Acción Inmediata   │
├─────────────────────────────────────┼──────────────────────┼────────────────────┤
│ FailedGetResourceMetric             │ Sin requests         │ Agregar requests   │
│                                     │ Metrics Server down  │ Instalar MS        │
│                                     │                      │                    │
│ FailedComputeMetricsReplicas        │ Datos corruptos      │ Esperar 2 min      │
│                                     │ División por cero    │ Agregar requests   │
│                                     │                      │                    │
│ DidNotScale                         │ En cooldown          │ Esperar 3-5 min    │
│                                     │ Dentro de rango      │ Normal, no actuar  │
│                                     │                      │                    │
│ TooManyReplicas                     │ maxReplicas muy bajo │ Aumentar max       │
│                                     │ o carga muy alta     │ u optimizar app    │
│                                     │                      │                    │
│ TooFewReplicas                      │ minReplicas muy alto │ Bajar min o HA req │
│                                     │ o carga muy baja     │ Normal en scale-dn │
│                                     │                      │                    │
│ FailedRescale                       │ RBAC insuficiente    │ Revisar RBAC       │
│                                     │ Pod Disruption Quota │ Revisar PDB        │
│                                     │                      │                    │
│ InvalidSelector                     │ Deployment no existe │ Verificar nombre   │
│                                     │ Namespace incorrecto │ o namespace        │
│                                     │                      │                    │
│ SuccessfulRescale                   │ ✓ Normal             │ Monitor que continúe│
│                                     │ Escalado exitoso     │ Revisar P95 latency│
│                                     │                      │                    │
│ FailedGetCustomMetric               │ Prometheus down      │ Revisar Prometheus │
│                                     │ Métrica no existe    │ Crear métrica      │
│                                     │                      │                    │
│ FailedGetExternalMetric             │ API externa down     │ Verificar provider │
│                                     │ Credenciales error   │ Revisar secretos   │
└─────────────────────────────────────┴──────────────────────┴────────────────────┘
```

---

## PARTE 4: SCRIPT DE DIAGNÓSTICO COMPLETO

```bash
#!/bin/bash
# hpa-diagnostic.sh - Diagnóstico completo de HPA

set -e

HPA_NAME="${1:-}"
NAMESPACE="${2:-default}"

if [ -z "$HPA_NAME" ]; then
  echo "Uso: $0 <hpa-name> [namespace]"
  exit 1
fi

echo "═════════════════════════════════════════════════════════════"
echo "DIAGNÓSTICO DE HPA: $HPA_NAME en $NAMESPACE"
echo "═════════════════════════════════════════════════════════════"

# SECCIÓN 1: Estado del HPA
echo -e "\n📊 ESTADO DEL HPA"
echo "─────────────────────────────────────────────────────────────"
kubectl get hpa $HPA_NAME -n $NAMESPACE -o wide
kubectl describe hpa $HPA_NAME -n $NAMESPACE | tail -20

# SECCIÓN 2: Eventos recientes
echo -e "\n⚠️  EVENTOS RECIENTES"
echo "─────────────────────────────────────────────────────────────"
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$HPA_NAME \
  --sort-by='.lastTimestamp' | tail -10

# SECCIÓN 3: Metrics Server
echo -e "\n🔧 METRICS SERVER"
echo "─────────────────────────────────────────────────────────────"
kubectl get deployment metrics-server -n kube-system 2>/dev/null && \
  echo "✓ Metrics Server instalado" || \
  echo "✗ Metrics Server NO INSTALADO"

# SECCIÓN 4: Métricas disponibles
echo -e "\n📈 MÉTRICAS DISPONIBLES"
echo "─────────────────────────────────────────────────────────────"
TARGET_REF=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.scaleTargetRef.name}')
kubectl top pods -n $NAMESPACE -l app=$TARGET_REF 2>/dev/null || \
  echo "⚠️  No hay métricas disponibles aún"

# SECCIÓN 5: Deployment/Requests
echo -e "\n🎯 DEPLOYMENT - RESOURCES"
echo "─────────────────────────────────────────────────────────────"
kubectl get deployment $TARGET_REF -n $NAMESPACE -o json | \
  jq '.spec.template.spec.containers[] | {name, resources}' 2>/dev/null || \
  echo "⚠️  No se encontró deployment"

# SECCIÓN 6: Pods estado
echo -e "\n🐳 ESTADO DE PODS"
echo "─────────────────────────────────────────────────────────────"
kubectl get pods -n $NAMESPACE -l app=$TARGET_REF -o wide

# SECCIÓN 7: API de métricas
echo -e "\n🌐 API DE MÉTRICAS (RAW)"
echo "─────────────────────────────────────────────────────────────"
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/$NAMESPACE/pods" 2>/dev/null | \
  jq '.items[] | {name: .metadata.name, cpu: .containers[0].usage.cpu, memory: .containers[0].usage.memory}' || \
  echo "✗ API de métricas no disponible"

# SECCIÓN 8: Cálculos manuales
echo -e "\n🧮 CÁLCULOS DE HPA"
echo "─────────────────────────────────────────────────────────────"
CURRENT_REPLICAS=$(kubectl get deployment $TARGET_REF -n $NAMESPACE -o jsonpath='{.status.replicas}')
MIN_REPLICAS=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
MAX_REPLICAS=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
TARGET_CPU=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.metrics[0].resource.target.averageUtilization}')

echo "Replicas actuales: $CURRENT_REPLICAS"
echo "Min replicas: $MIN_REPLICAS"
echo "Max replicas: $MAX_REPLICAS"
echo "Target CPU: $TARGET_CPU%"

echo -e "\n═════════════════════════════════════════════════════════════"
echo "DIAGNOSIS COMPLETO"
echo "═════════════════════════════════════════════════════════════"
```

**Uso:**

```bash
chmod +x hpa-diagnostic.sh
./hpa-diagnostic.sh nginx-hpa default
```

---

## PARTE 5: REFERENCIA DE CONCEPTOS TEÓRICOS

### El Algoritmo de HPA (RFC Formal)

**Especificación Kubernetes:**

```
DesiredReplicas = ceil(
    Σ(CurrentMetricValue[pod] / TargetMetricValue) 
    × CurrentReplicas
)

Donde:
- CurrentMetricValue = métrica actual del pod (ej: 80m CPU)
- TargetMetricValue = target configurado (ej: 100m CPU = 100%)
- CurrentReplicas = número actual de pods (ej: 3)

Restricciones:
- Si DesiredReplicas < minReplicas → usar minReplicas
- Si DesiredReplicas > maxReplicas → usar maxReplicas
- Si DesiredReplicas == CurrentReplicas → no cambiar (DidNotScale)
```

**Ejemplo Concreto:**

```
Escenario:
- 3 pods de nginx
- Cada pod tiene requests.cpu = 100m
- CPU target = 70% (100m × 0.70 = 70m actual objetivo)
- Métrica actual: CPU promedio = 140m

Cálculo:
DesiredReplicas = ceil((140m / 100m) × 3)
                = ceil(1.4 × 3)
                = ceil(4.2)
                = 5

Acción: Scale 3 → 5 pods
Evento: SuccessfulRescale
Mensaje: "New size: 5; reason: cpu resource utilization (percentage of request: 140%)"
```

### Estados Posibles de HPA

```
┌─────────────────────────────────────────────────────┐
│              HPA STATE MACHINE                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │   SCALING_UP (Cooldown 3 min)               │   │
│  │   SuccessfulRescale → TooManyReplicas?      │   │
│  └──────────────────┬──────────────────────────┘   │
│                     │                               │
│                     ▼                               │
│  ┌─────────────────────────────────────────────┐   │
│  │   IDLE (Esperando cambio de métricas)       │   │
│  │   DidNotScale → métrica en rango target     │   │
│  └──────────────────┬──────────────────────────┘   │
│                     │                               │
│                     ▼                               │
│  ┌─────────────────────────────────────────────┐   │
│  │   SCALING_DOWN (Cooldown 5 min)             │   │
│  │   SuccessfulRescale → TooFewReplicas?       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ERRORES (cualquier estado):                       │
│  - FailedGetResourceMetric                         │
│  - FailedComputeMetricsReplicas                    │
│  - FailedRescale                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Cooldown Windows (Crucial para Entender Events)

```yaml
Escala Up (Scale Up Cooldown):
  Después de cambiar de X → Y replicas, esperar 3 minutos
  antes de volver a escalar hacia arriba
  
  Razón: Evitar que la métrica suba más (más pods = menos carga por pod)
  
  Timeline:
  T=0m   Escala 3→5
  T=3m   Puede volver a escalar si sigue alto
  T=3m30s Continúa monitoreo

Escala Down (Scale Down Cooldown):
  Después de cambiar de X → Y replicas, esperar 5 minutos
  antes de volver a escalar hacia abajo
  
  Razón: Evitar desperdicio de recursos si habrá picos pronto
  
  Timeline:
  T=0m   Escala 5→3
  T=5m   Puede volver a escalar hacia abajo si sigue bajo
```

**En el evento `DidNotScale`, verás:**

```
Message: "the desired replica count is less than the current 
replica count and one or both of the 
--horizontal-pod-autoscaler-downscale-stabilization lower bound 
is preventing scale-down"

↑ Significa que está esperando el cooldown de 5 minutos
```

---

## RESUMEN PROFESIONAL

### Para CKA Exam

| Evento | Tipo | Causa | Solución |
|--------|------|-------|----------|
| `FailedGetResourceMetric` | ⚠️ Warning | Metrics Server down, sin requests | Instalar MS, agregar requests |
| `ScalingReplicaSet` | ✓ Success | Escalado exitoso | Ninguna, es normal |
| `DidNotScale` | ✓ Success | En rango, sin cambio | Ninguna, es normal |
| `TooManyReplicas` | ⚠️ Warning | Carga alta, maxReplicas insuficiente | Aumentar max o optimizar |
| `FailedComputeMetrics` | ⚠️ Warning | Datos malformados | Esperar, revisar requests |
| `InvalidSelector` | ⚠️ Warning | Deployment no existe | Verificar nombre/namespace |

### Para Operación Diaria

1. **Monitorea eventos constantemente:**
   ```bash
   kubectl get events -n prod --sort-by='.lastTimestamp' --watch
   ```

2. **Configura alertas para:**
   - `TooManyReplicas` > 5 minutos
   - `FailedGetResourceMetric` consecutivos
   - `FailedRescale` cualquier ocurrencia

3. **Valida tus HPAs:**
   ```bash
   kubectl get hpa -A -o json | jq '.items[] | select(.spec.minReplicas < 2)'
   ```

4. **Documenta tus configuraciones:**
   - Por qué ese minReplicas/maxReplicas
   - Por qué ese target %
   - Expected behavior bajo carga