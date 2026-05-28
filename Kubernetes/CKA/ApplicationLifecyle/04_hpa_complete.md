# HORIZONTAL POD AUTOSCALING (HPA) EN KUBERNETES
## Guía Completa Teórico-Práctica para Platform Engineers

**Versión:** 2.0 (2026)  
**Audiencia:** Developers, DevOps, Platform Engineers, SREs  
**Nivel:** Introductorio a Avanzado  
**Scope:** Kubernetes 1.20+

---

## TABLA DE CONTENIDOS

1. [Fundamentos Teóricos](#1-fundamentos-teóricos)
2. [Arquitectura y Componentes](#2-arquitectura-y-componentes)
3. [Configuración Práctica](#3-configuración-práctica)
4. [Gobernanza y Estándares](#4-gobernanza-y-estándares)
5. [Observabilidad y Monitoreo](#5-observabilidad-y-monitoreo)
6. [Eventos de HPA](#6-eventos-de-hpa)
7. [Troubleshooting](#7-troubleshooting)
8. [Runbooks](#8-runbooks)
9. [Casos de Uso](#9-casos-de-uso)
10. [Cost Optimization](#10-cost-optimization)
11. [Testing y Validación](#11-testing-y-validación)
12. [Integración con Cluster Autoscaling](#12-integración-con-cluster-autoscaling)
13. [Checklist de Implementación](#13-checklist-de-implementación)

---

# 1. FUNDAMENTOS TEÓRICOS

## 1.1 ¿Qué es HPA?

**Horizontal Pod Autoscaling (HPA)** es un mecanismo automático en Kubernetes que **ajusta el número de pods de una aplicación** basándose en métricas observadas, permitiendo que el sistema responda dinámicamente a cambios en la demanda.

### Diferencias Fundamentales

| Característica | HPA (Horizontal) | VPA (Vertical) |
|---|---|---|
| **Qué escala** | Número de pods | Recursos por pod |
| **Eje de escalado** | Horizontal (más instancias) | Vertical (más potentes) |
| **Implementación** | `autoscaling/v2` | `autoscaling.k8s.io/v1` |
| **Aplicación típica** | APIs stateless | Aplicaciones con picos |
| **Ventaja principal** | HA, distribución de carga | Simplifica configuración |
| **Desventaja** | Requiere stateless | Sin garantía de latencia |

### Conceptos Clave

**1. Escalado Horizontal (HPA):**
```
Antes:  ┌─────┐┌─────┐┌─────┐
        │ Pod │││ Pod │││ Pod │  (3 replicas, CPU=90%)
        └─────┘└─────┘└─────┘
                    ↓ HPA
Después:┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
        │ Pod │││ Pod │││ Pod │││ Pod │││ Pod │  (5 replicas, CPU=54%)
        └─────┘└─────┘└─────┘└─────┘└─────┘
```

**2. Métrica de Utilización:**
```
Utilización (%) = (Uso Actual / Requests) × 100

Ejemplo:
- Container: requests.cpu = 100m
- Uso actual: 75m de CPU
- Utilización: (75m / 100m) × 100 = 75%
```

**3. Fórmula de Cálculo de Replicas:**
```
desiredReplicas = ceil(
    (sumaMetricaActual / sumaMetricaTarget) × replicasActuales
)

Donde:
- sumaMetricaActual = suma de CPU de todos los pods
- sumaMetricaTarget = (requests × targetPercentage) × replicasActuales
```

## 1.2 Ciclo de Operación

```
╔═══════════════════════════════════════════════════════════════╗
║                    CICLO DE HPA (15 segundos)                ║
╚═══════════════════════════════════════════════════════════════╝

T=0s    ┌─────────────────────────────────────────────────┐
        │ 1. HPA Controller consulta Metrics Server        │
        │    GET /apis/metrics.k8s.io/v1beta1/...         │
        └────────────────┬────────────────────────────────┘
                         ▼
T=1s    ┌─────────────────────────────────────────────────┐
        │ 2. Obtiene métricas actuales de todos los pods  │
        │    cpu: 85m, 92m, 78m (promedio: 85m)          │
        └────────────────┬────────────────────────────────┘
                         ▼
T=2s    ┌─────────────────────────────────────────────────┐
        │ 3. Compara con target                           │
        │    actual: 85m, target: 70m (70% de 100m)       │
        │    ratio: 85/70 = 1.21                          │
        └────────────────┬────────────────────────────────┘
                         ▼
T=3s    ┌─────────────────────────────────────────────────┐
        │ 4. Calcula replicas deseadas                    │
        │    desiredReplicas = ceil(1.21 × 3) = 4         │
        │    (cambiar de 3 a 4 replicas)                  │
        └────────────────┬────────────────────────────────┘
                         ▼
T=4s    ┌─────────────────────────────────────────────────┐
        │ 5. Verifica restricciones                       │
        │    min: 2 ≤ 4 ≤ max: 10 ✓ OK                   │
        └────────────────┬────────────────────────────────┘
                         ▼
T=5s    ┌─────────────────────────────────────────────────┐
        │ 6. Ejecuta cambio si es necesario               │
        │    kubectl patch deployment ...                 │
        │    Event: SuccessfulRescale                     │
        └────────────────┬────────────────────────────────┘
                         ▼
T=6s    ┌─────────────────────────────────────────────────┐
        │ 7. Inicia cooldown                              │
        │    - Scale Up: 3 minutos                        │
        │    - Scale Down: 5 minutos                      │
        └─────────────────────────────────────────────────┘

Nota: Este ciclo se repite cada 15 segundos (--horizontal-pod-autoscaler-sync-period)
```

## 1.3 Estados y Transiciones

```
┌──────────────────────────────────────┐
│      Estado: IDLE                    │
│  (Métrica dentro del rango target)   │
│  Evento: DidNotScale                 │
└────────────┬───────────────────┬─────┘
             │                   │
             │ CPU > target      │ CPU < target
             │                   │
        ┌────▼────────────┐  ┌──▼──────────────┐
        │  SCALING UP     │  │  SCALING DOWN   │
        │  (3 min CW)     │  │  (5 min CW)     │
        │  +2→5 replicas  │  │  -5→2 replicas  │
        │  Evento: Scale  │  │  Evento: Scale  │
        │  ReplicaSet     │  │  ReplicaSet     │
        └────┬───────────┘   └───┬─────────────┘
             │                   │
             └───────┬───────────┘
                     │
                ┌────▼────────────────┐
                │  COOLDOWN PERIOD    │
                │  (Esperar 3-5 min)  │
                │  Siguiente cambio   │
                │  permitido después  │
                └─────────────────────┘
```

---

# 2. ARQUITECTURA Y COMPONENTES

## 2.1 Componentes de HPA

```
┌────────────────────────────────────────────────────────────────┐
│                   CONTROL PLANE (Master)                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────┐        ┌──────────────────────┐    │
│  │  API Server          │◄──────►│  Metrics Server      │    │
│  │  - Stored HPA        │        │  - Agregador métricas│    │
│  │  - Validación        │        │  - API REST metrics  │    │
│  └──────────────────────┘        └──────────────────────┘    │
│                                                                │
│  ┌──────────────────────┐                                     │
│  │  HPA Controller      │                                     │
│  │  (autoscaling-      │                                      │
│  │   controller-manager)                                      │
│  │  - Consulta métricas │                                     │
│  │  - Calcula replicas  │                                     │
│  │  - Aplica cambios    │                                     │
│  └──────┬───────────────┘                                     │
│         │                                                      │
│         │ PATCH deployment.spec.replicas                      │
│         ▼                                                      │
│  ┌──────────────────────┐                                     │
│  │  etcd                │                                     │
│  │  (Stored state)      │                                     │
│  └──────────────────────┘                                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
         ▲
         │ Reporte de cambios
         │
┌────────▼─────────────────────────────────────────────────────┐
│              WORKER NODES                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Node 1          Node 2          Node 3                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Pod A      │  │ Pod B      │  │ Pod C      │            │
│  │ CPU: 75m   │  │ CPU: 92m   │  │ CPU: 78m   │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │                │               │                    │
│  ┌─────▼──────┐  ┌──────▼────────┐ ┌──▼────────┐           │
│  │  Kubelet   │  │   Kubelet     │ │ Kubelet   │           │
│  │ (cgroup)   │  │   (cgroup)    │ │ (cgroup)  │           │
│  └─────┬──────┘  └──────┬────────┘ └──┬────────┘           │
│        │                │               │                    │
│        └────────┬───────┴───────────────┘                   │
│                 │                                            │
│         Metrics recopiladas                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                 SECUENCIA TEMPORAL                          │
└─────────────────────────────────────────────────────────────┘

T = 0-15s:
├─ Kubelet → Metrics Server: cgroup stats (CPU, Memory)
├─ Metrics Server calcula: Σ(cpu) / número_containers
└─ Expone en: /apis/metrics.k8s.io/v1beta1/nodes/pods

T = 15s (every --horizontal-pod-autoscaler-sync-period):
├─ HPA Controller: GET /apis/metrics.k8s.io/v1beta1/...
├─ Recibe: {cpu: 85m, memory: 256Mi}
├─ Calcula: desiredReplicas = ceil((85/100) × 3) = 3
├─ Verifica: 2 ≤ 3 ≤ 10 ✓
└─ Si cambio: PATCH /apis/apps/v1/.../replicas

T = 16s:
├─ ReplicaSet Controller: Actualiza replicas
├─ Scheduler: Asigna Pods a Nodos
└─ Kubelet: Crea contenedores

T = 30s:
├─ Nuevos Pods reportan metrics
├─ Metrics Server recalcula promedio
└─ HPA verifica nuevamente
```

---

# 3. CONFIGURACIÓN PRÁCTICA

## 3.1 Requisitos Previos

### Instalación de Metrics Server

```bash
# Verificar si está instalado
kubectl get deployment metrics-server -n kube-system

# Si no existe, instalar versión última
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verificar que está corriendo
kubectl wait --for=condition=available --timeout=300s deployment/metrics-server -n kube-system

# Verificar que proporciona métricas
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes | jq '.items[0]'
```

### Verificar Permisos

```bash
# El HPA Controller necesita:
# - get/list/watch: horizontalpodautoscalers
# - get/list: deployments, statefulsets, replicasets
# - update: deployments/scale, statefulsets/scale

kubectl auth can-i update deployment/nginx --as=system:serviceaccount:kube-system:horizontal-pod-autoscaler
# Debe retornar: yes
```

## 3.2 HPA Simple (v1 - Deprecated)

```yaml
# ⚠️ DEPRECATED en Kubernetes 1.23+
# Solo para legado, NO usar en nuevos deployments

apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: simple-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-app
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

**Limitaciones:**
- Solo soporta CPU
- No soporta múltiples métricas
- No soporta métricas personalizadas

## 3.3 HPA Moderno (v2)

### 3.3.1 HPA Basado en CPU

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
  namespace: production
  labels:
    app: my-app
    managed-by: platform-team
spec:
  # ¿Qué escalar?
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  
  # Límites de replicas
  minReplicas: 2              # Nunca menos de 2 (HA)
  maxReplicas: 50             # Máximo permitido
  
  # Métrica de escalado
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization      # Porcentaje de requests
        averageUtilization: 75  # Target: 75%
  
  # Comportamiento de escalado
  behavior:
    # Scale Up (agregar pods)
    scaleUp:
      stabilizationWindowSeconds: 0    # Escalar rápido
      policies:
      - type: Percent                  # Aumentar 100% (duplicar)
        value: 100
        periodSeconds: 30               # Cada 30 segundos
      - type: Pods                      # O máximo 4 pods nuevos
        value: 4
        periodSeconds: 30
      selectPolicy: Max                 # Usa el que more agregue
    
    # Scale Down (remover pods)
    scaleDown:
      stabilizationWindowSeconds: 300  # Esperar 5 minutos
      policies:
      - type: Percent                  # Reducir máximo 50%
        value: 50
        periodSeconds: 60
```

### 3.3.2 HPA con CPU y Memoria

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: advanced-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 100
  
  # Múltiples métricas (OR lógico)
  # Si CUALQUIERA está fuera de target, HPA actúa
  metrics:
  
  # Métrica 1: CPU
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # Métrica 2: Memoria
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 5
        periodSeconds: 30
      selectPolicy: Max
```

### 3.3.3 HPA con Métricas Personalizadas (Prometheus)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: custom-metric-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2
  maxReplicas: 50
  
  metrics:
  # Métrica personalizada de Prometheus
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
        selector:
          matchLabels:
            metric_type: throughput
      target:
        type: AverageValue
        averageValue: "1000"    # 1000 req/s por pod
  
  # Fallback a CPU
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### 3.3.4 HPA con Métricas Externas

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: queue-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: worker
  minReplicas: 1
  maxReplicas: 100
  
  metrics:
  # Escalar basado en profundidad de cola (SQS, RabbitMQ)
  - type: External
    external:
      metric:
        name: sqs_queue_depth
        selector:
          matchLabels:
            queue_name: "process-jobs"
      target:
        type: AverageValue
        averageValue: "30"      # 30 mensajes por worker
```

## 3.4 Deployment con Requests/Limits

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:v1
        
        # ⚠️ CRÍTICO: Sin esto, HPA no funciona
        resources:
          requests:              # Garantizado
            cpu: 100m           # 0.1 cores
            memory: 128Mi       # 128 megabytes
          limits:               # Máximo
            cpu: 500m           # 0.5 cores
            memory: 512Mi       # 512 megabytes
        
        # Health checks para escalado correcto
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 3
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
      
      # Para escalar correctamente
      terminationGracePeriodSeconds: 30
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - my-app
              topologyKey: kubernetes.io/hostname
```

## 3.5 Pod Disruption Budget (Necesario para HPA)

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 1          # Mínimo 1 pod disponible siempre
  selector:
    matchLabels:
      app: my-app
```

---

# 4. GOBERNANZA Y ESTÁNDARES

## 4.1 Política Organizacional

```yaml
# kube-system/hpa-policy.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hpa-organization-policy
  namespace: kube-system
data:
  policy: |
    {
      "minReplicas": {
        "minimum": 2,
        "rationale": "Garantizar Alta Disponibilidad (HA)"
      },
      "maxReplicas": {
        "maximum": 100,
        "rationale": "Evitar crecimiento exponencial y controlar costos"
      },
      "targetCPUUtilization": {
        "default": 70,
        "range": [50, 90],
        "rationale": "Balance entre eficiencia y headroom"
      },
      "targetMemoryUtilization": {
        "default": 75,
        "range": [60, 85],
        "rationale": "Evitar OOMKill"
      },
      "requiredMetrics": 2,
      "requiredHealthChecks": true,
      "requiredPDB": true
    }
```

## 4.2 Validación con Admission Controller

```python
# hpa-validator-webhook.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/validate', methods=['POST'])
def validate_hpa():
    admission_review = request.get_json()
    hpa = admission_review['request']['object']
    
    errors = []
    
    # Validación 1: minReplicas >= 2
    if hpa['spec']['minReplicas'] < 2:
        errors.append("minReplicas must be >= 2 (HA requirement)")
    
    # Validación 2: maxReplicas <= 100
    if hpa['spec']['maxReplicas'] > 100:
        errors.append("maxReplicas must be <= 100")
    
    # Validación 3: Al menos 2 métricas
    if len(hpa['spec'].get('metrics', [])) < 2:
        errors.append("At least 2 metrics required (e.g., CPU + Memory)")
    
    # Validación 4: Deployment tiene requests
    deployment = get_deployment(hpa['spec']['scaleTargetRef'])
    for container in deployment['spec']['template']['spec']['containers']:
        resources = container.get('resources', {})
        requests = resources.get('requests', {})
        
        if 'cpu' not in requests:
            errors.append(f"Container {container['name']} missing requests.cpu")
        
        if 'memory' not in requests:
            errors.append(f"Container {container['name']} missing requests.memory")
    
    if errors:
        return jsonify({
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': admission_review['request']['uid'],
                'allowed': False,
                'status': {
                    'code': 400,
                    'message': '; '.join(errors)
                }
            }
        }), 400
    
    return jsonify({
        'apiVersion': 'admission.k8s.io/v1',
        'kind': 'AdmissionReview',
        'response': {
            'uid': admission_review['request']['uid'],
            'allowed': True
        }
    })

if __name__ == '__main__':
    app.run(ssl_context='adhoc', port=8443)
```

## 4.3 Template Estándar (Helm)

```yaml
# helm/values.yaml
global:
  namespace: default

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  metrics:
    cpu:
      enabled: true
      targetUtilization: 70
    memory:
      enabled: true
      targetUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

---

# 5. OBSERVABILIDAD Y MONITOREO

## 5.1 Métricas Prometheus

### Registrar Eventos de HPA

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-hpa-config
  namespace: monitoring
data:
  hpa-recording.yml: |
    groups:
    - name: hpa_metrics
      interval: 30s
      rules:
      
      # Tasa de escalado
      - record: hpa:scaling_rate:1m
        expr: rate(kube_deployment_status_replicas[1m])
      
      # Replicas como % de máximo
      - record: hpa:replica_saturation
        expr: kube_deployment_status_replicas / kube_deployment_spec_replicas_max * 100
      
      # Variabilidad de replicas
      - record: hpa:replica_variance:5m
        expr: stddev(kube_deployment_status_replicas[5m])
      
      # CPU utilization
      - record: hpa:cpu_utilization
        expr: >
          sum(rate(container_cpu_usage_seconds_total{pod=~".*"}[1m])) by (deployment)
          / sum(kube_pod_container_resource_requests{resource="cpu"}) by (deployment)
          * 100
```

## 5.2 Alertas Críticas (PrometheusRule)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: hpa-alerts
  namespace: monitoring
spec:
  groups:
  - name: hpa.alerts
    interval: 30s
    rules:
    
    # ALERTA 1: HPA alcanza máximo
    - alert: HPAAtMaxReplicas
      expr: |
        kube_deployment_status_replicas == kube_deployment_spec_replicas_max
      for: 5m
      severity: warning
      labels:
        component: hpa
      annotations:
        summary: "{{ $labels.deployment }} está en máximo de replicas"
        description: "HPA en {{ $labels.namespace }}/{{ $labels.deployment }} ha estado en máximo por 5 minutos. Posible cuello de botella."
        runbook: "https://wiki.company.com/runbooks/hpa-at-max-replicas"
        dashboard: "https://grafana.company.com/d/hpa-debug/hpa-debug?var-deployment={{ $labels.deployment }}"
    
    # ALERTA 2: Sin métricas de CPU
    - alert: HPAMissingCPUMetrics
      expr: |
        absent(container_cpu_usage_seconds_total{pod=~".*"}) == 1
      for: 2m
      severity: critical
      annotations:
        summary: "Metrics Server no proporciona CPU para {{ $labels.pod }}"
        description: "Sin métricas de CPU disponibles. Verificar Metrics Server."
        runbook: "https://wiki.company.com/runbooks/metrics-server-down"
    
    # ALERTA 3: HPA oscila (Flapping)
    - alert: HPAFlapping
      expr: |
        stddev(increase(kube_deployment_status_replicas[1m])) > 2
      for: 10m
      severity: warning
      annotations:
        summary: "{{ $labels.deployment }} oscila entre replicas"
        description: "El número de replicas cambia constantemente. Revisar stabilizationWindow o target."
    
    # ALERTA 4: Fallos de escalado
    - alert: HPAScalingFailure
      expr: |
        increase(kube_hpa_status_current_replicas[10m]) == 0
        and
        kube_deployment_status_replicas > kube_deployment_spec_replicas
      for: 5m
      severity: critical
      annotations:
        summary: "HPA no logra escalar {{ $labels.deployment }}"
        description: "HPA está intentando escalar pero los pods no inician. Verificar recursos de nodos."
    
    # ALERTA 5: Costo diario excedido
    - alert: ComputeCostExceeded
      expr: |
        (sum(rate(container_cpu_usage_seconds_total[1m])) * 3.6 * $cpu_hourly_cost +
         sum(container_memory_working_set_bytes) / 1024^3 * $mem_hourly_cost) * 24 > $daily_budget
      for: 30m
      severity: warning
      annotations:
        summary: "Costo diario de compute excede presupuesto"
        description: "Gasto actual: ${{ $value }}/día"
```

## 5.3 Dashboard Grafana

```json
{
  "dashboard": {
    "title": "HPA Monitoring - Organization Wide",
    "tags": ["hpa", "autoscaling", "kubernetes"],
    "refresh": "30s",
    "panels": [
      {
        "title": "Replicas Actuales vs Target",
        "targets": [
          {
            "expr": "kube_deployment_status_replicas{namespace=~\"$namespace\", deployment=~\"$deployment\"}"
          }
        ]
      },
      {
        "title": "CPU Utilization % vs Target",
        "targets": [
          {
            "expr": "hpa:cpu_utilization{namespace=~\"$namespace\", deployment=~\"$deployment\"}"
          }
        ]
      },
      {
        "title": "Scaling Events (últimas 24h)",
        "targets": [
          {
            "expr": "increase(kube_deployment_status_replicas[1h]) > 0"
          }
        ]
      },
      {
        "title": "Deployments en maxReplicas",
        "targets": [
          {
            "expr": "kube_deployment_status_replicas == kube_deployment_spec_replicas_max"
          }
        ]
      },
      {
        "title": "Estabilidad de Replicas",
        "targets": [
          {
            "expr": "hpa:replica_variance:5m{namespace=~\"$namespace\"}"
          }
        ]
      }
    ]
  }
}
```

---

# 6. EVENTOS DE HPA

## 6.1 Matriz Completa de Eventos

### Categoría 1: Éxito

```
Evento: SuccessfulRescale
├─ Type: Normal
├─ Reason: Escalado exitoso
├─ Ejemplo: "New size: 5; reason: cpu resource utilization (percentage of request: 85%)"
└─ Acción: Continuar monitoreando

Evento: DidNotScale
├─ Type: Normal
├─ Reason: Métrica dentro del rango, sin cambio necesario
├─ Ejemplo: "the desired replica count is less than the current replica count and..."
└─ Acción: NORMAL, no intervenir
```

### Categoría 2: Fallos de Métricas

```
Evento: FailedGetResourceMetric ⚠️
├─ Causa Raíz:
│  ├─ 1. Metrics Server no instalado
│  ├─ 2. Metrics Server en CrashLoop
│  ├─ 3. Pod sin requests definidos ⭐ COMÚN
│  ├─ 4. Kubelet no reporta métricas
│  ├─ 5. Pod en estado Pending
│  └─ 6. Network Policy bloqueando
├─ Diagnóstico:
│  ├─ kubectl get deployment -n kube-system metrics-server
│  ├─ kubectl get deployment <name> -o yaml | grep -A5 resources
│  └─ kubectl logs -n kube-system -l k8s-app=metrics-server
└─ Solución: Instalar MS + Agregar requests

Evento: FailedComputeMetricsReplicas ⚠️
├─ Causa: Datos de métrica corrupto o inválido
├─ Ejemplo: "missing request for cpu" (sin requests)
└─ Solución: Esperar 2 min, agregar requests

Evento: FailedGetCustomMetric ⚠️
├─ Causa: Métrica personalizada no disponible (Prometheus)
├─ Ejemplo: "http_requests_per_second not found"
└─ Solución: Verificar Prometheus, crear métrica

Evento: FailedGetExternalMetric ⚠️
├─ Causa: API externa no disponible
├─ Ejemplo: "unable to get external metrics API"
└─ Solución: Verificar proveedor cloud, credenciales
```

### Categoría 3: Restricciones

```
Evento: TooManyReplicas ⚠️
├─ Causa: Cálculo excede maxReplicas
├─ Mensaje: "the desired replica count 150 exceeds the maximum replica count 100"
└─ Solución:
   ├─ Temporal: Aumentar maxReplicas
   └─ Permanente: Optimizar app

Evento: TooFewReplicas ⚠️
├─ Causa: Cálculo < minReplicas
├─ Mensaje: "the desired replica count 1 is less than the minimum replica count 2"
└─ Acción: NORMAL si es scale-down
```

### Categoría 4: Configuración

```
Evento: FailedRescale ⚠️
├─ Causa: No se puede cambiar replicas
│  ├─ RBAC insuficiente
│  ├─ Pod Disruption Quota alcanzada
│  └─ Resource Quota excedida
├─ Mensaje: "failed to rescale deployment: Forbidden"
└─ Solución: Revisar RBAC, PDB, Quotas

Evento: InvalidSelector ⚠️
├─ Causa: scaleTargetRef apunta a recurso inexistente
├─ Mensaje: "unable to get target: not found"
└─ Solución: Verificar nombre y namespace del deployment

Evento: InvalidTargetResourceUnitFormat ⚠️
├─ Causa: Formato inválido en métrica
└─ Solución: Corregir YAML
```

## 6.2 Flujo de Diagnóstico

```
Síntoma: HPA no escala

├─ Paso 1: Ver estado de HPA
│  └─ kubectl describe hpa <name>
│     ├─ ¿Dice "unknown" en TARGETS?
│     │  └─ Problema: Métricas no disponibles
│     └─ ¿Dice valores (%) en TARGETS?
│        └─ Métricas OK
│
├─ Paso 2: Revisar eventos
│  └─ kubectl get events -A | grep <hpa-name>
│     ├─ ¿FailedGetResourceMetric?
│     │  ├─ ¿Metrics Server existe?
│     │  │  └─ kubectl get deployment -n kube-system metrics-server
│     │  └─ ¿Pod tiene requests?
│     │     └─ kubectl get deployment <> -o yaml | grep requests
│     ├─ ¿DidNotScale?
│     │  └─ NORMAL: métrica dentro de rango
│     ├─ ¿FailedRescale?
│     │  ├─ ¿RBAC?
│     │  └─ ¿PDB?
│     └─ ¿Ninguno?
│        └─ Esperar 2 minutos (latencia de métricas)
│
└─ Paso 3: Ejecutar diagnóstico completo
   └─ ./hpa-diagnostic.sh <name>
```

---

# 7. TROUBLESHOOTING

## 7.1 Problemas Comunes y Soluciones

### Problema 1: HPA muestra "unknown" en TARGETS

```bash
# Síntoma
$ kubectl get hpa
NAME        REFERENCE                  TARGETS         MINPODS MAXPODS REPLICAS
app-hpa     Deployment/app             unknown         2       10      2

# Causa 1: Metrics Server no existe
kubectl get deployment -n kube-system metrics-server
# Si no existe:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Causa 2: Deployment sin requests
kubectl get deployment app -o json | jq '.spec.template.spec.containers[].resources.requests'
# Si está vacío (null):
kubectl set resources deployment app --requests=cpu=100m,memory=128Mi

# Causa 3: Latencia (pod muy nuevo)
# Esperar 1-2 minutos y reintentarq

# Diagnost total
kubectl describe hpa app-hpa
kubectl get events -n default --field-selector involvedObject.name=app-hpa
```

### Problema 2: HPA oscila constantemente

```bash
# Síntoma: Replicas saltan constantemente (3→5→3→5...)

# Causa: stabilizationWindow demasiado bajo

# Solución: Aumentar ventana de estabilización
kubectl patch hpa app-hpa -p '
{
  "spec": {
    "behavior": {
      "scaleDown": {
        "stabilizationWindowSeconds": 300,
        "policies": [{"type": "Percent", "value": 50, "periodSeconds": 60}]
      }
    }
  }
}
'

# Validar cambio
kubectl describe hpa app-hpa
```

### Problema 3: HPA alcanza maxReplicas constantemente

```bash
# Síntoma: REPLICAS = 100 (igual a MAXPODS)

# Opción 1: TEMPORAL - Aumentar máximo
kubectl patch hpa app-hpa -p '{"spec":{"maxReplicas":200}}'

# Opción 2: PERMANENTE - Optimizar aplicación
# - Profiling: ¿Dónde se gasta CPU?
#   kubectl exec -it pod -- go tool pprof http://localhost:6060/debug/pprof/profile
# - Optimizar DB queries
# - Implementar caching
# - Mejorar algoritmos

# Opción 3: INFRAESTRUCTURA - Escalar nodos
# Cluster Autoscaler debería detectar pods Pending
kubectl get pods -o wide | grep Pending
kubectl describe pod <pending-pod>  # Ver razón
```

### Problema 4: RBAC insuficiente

```bash
# Síntoma: Evento FailedRescale

# Verificar permisos actuales
kubectl auth can-i update deployment/app --as=system:serviceaccount:kube-system:horizontal-pod-autoscaler
# Debe decir: yes

# Si dice no, agregar permisos
kubectl create clusterrolebinding hpa-deployment-rescaler \
  --clusterrole=edit \
  --serviceaccount=kube-system:horizontal-pod-autoscaler

# Mejor: Usar rol específico
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: hpa-rescaler
rules:
- apiGroups: ["apps"]
  resources: ["deployments/scale", "statefulsets/scale"]
  verbs: ["update", "patch"]
EOF

kubectl create clusterrolebinding hpa-rescaler-binding \
  --clusterrole=hpa-rescaler \
  --serviceaccount=kube-system:horizontal-pod-autoscaler
```

### Problema 5: Pod Disruption Budget bloqueando

```bash
# Síntoma: HPA quiere escalar down pero PDB previene

# Ver PDB
kubectl get poddisruptionbudget

# Si minAvailable es muy alto:
kubectl patch pdb my-app-pdb -p '{"spec":{"minAvailable":1}}'

# Mejor: Usar maxUnavailable
cat <<EOF | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  maxUnavailable: 1    # Máximo 1 pod disrupted
  selector:
    matchLabels:
      app: my-app
EOF
```

## 7.2 Script de Diagnóstico Automático

```bash
#!/bin/bash
# hpa-diagnostic.sh

set -e

HPA_NAME="${1:-}"
NAMESPACE="${2:-default}"

if [ -z "$HPA_NAME" ]; then
  echo "Uso: $0 <hpa-name> [namespace]"
  exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "DIAGNÓSTICO COMPLETO DE HPA: $HPA_NAME"
echo "═══════════════════════════════════════════════════════════════"

# SECCIÓN 1: Estado del HPA
echo -e "\n📊 ESTADO DEL HPA"
echo "─────────────────────────────────────────────────────────────"
kubectl get hpa $HPA_NAME -n $NAMESPACE
echo ""
kubectl describe hpa $HPA_NAME -n $NAMESPACE | grep -A 20 "^Metrics:"

# SECCIÓN 2: Eventos recientes
echo -e "\n⚠️  EVENTOS RECIENTES (últimos 20)"
echo "─────────────────────────────────────────────────────────────"
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$HPA_NAME \
  --sort-by='.lastTimestamp' | tail -20

# SECCIÓN 3: Verificar Metrics Server
echo -e "\n🔧 METRICS SERVER"
echo "─────────────────────────────────────────────────────────────"
if kubectl get deployment metrics-server -n kube-system &>/dev/null; then
    echo "✓ Metrics Server instalado"
    kubectl get deployment metrics-server -n kube-system
    echo ""
    kubectl logs -n kube-system -l k8s-app=metrics-server | tail -5
else
    echo "✗ ERROR: Metrics Server NO INSTALADO"
fi

# SECCIÓN 4: Verificar deployment target
echo -e "\n🎯 DEPLOYMENT TARGET"
echo "─────────────────────────────────────────────────────────────"
TARGET=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.scaleTargetRef.name}')
echo "Deployment: $TARGET"

if kubectl get deployment $TARGET -n $NAMESPACE &>/dev/null; then
    echo "✓ Deployment encontrado"
    kubectl get deployment $TARGET -n $NAMESPACE
    
    # Verificar requests
    echo -e "\nResources/Requests:"
    kubectl get deployment $TARGET -n $NAMESPACE -o json | \
      jq '.spec.template.spec.containers[] | {name, resources}'
else
    echo "✗ ERROR: Deployment no encontrado"
fi

# SECCIÓN 5: Métricas disponibles
echo -e "\n📈 MÉTRICAS DISPONIBLES"
echo "─────────────────────────────────────────────────────────────"
if kubectl top pods -n $NAMESPACE -l app=$TARGET &>/dev/null 2>&1; then
    kubectl top pods -n $NAMESPACE -l app=$TARGET
else
    echo "⚠️  No hay métricas disponibles aún (esperar 1-2 minutos)"
fi

# SECCIÓN 6: Pods status
echo -e "\n🐳 ESTADO DE PODS"
echo "─────────────────────────────────────────────────────────────"
kubectl get pods -n $NAMESPACE -l app=$TARGET -o wide

# SECCIÓN 7: Verificar API de métricas (raw)
echo -e "\n🌐 API DE MÉTRICAS (RAW)"
echo "─────────────────────────────────────────────────────────────"
if kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/$NAMESPACE/pods" &>/dev/null; then
    echo "✓ API de métricas disponible"
    kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/$NAMESPACE/pods" 2>/dev/null | \
      jq '.items[0:2] | .[] | {name: .metadata.name, cpu: .containers[0].usage.cpu, memory: .containers[0].usage.memory}' || \
      echo "Error parsing metrics"
else
    echo "✗ API de métricas NO disponible"
fi

# SECCIÓN 8: Cálculos manuales
echo -e "\n🧮 CÁLCULOS DEL HPA"
echo "─────────────────────────────────────────────────────────────"
CURRENT=$(kubectl get deployment $TARGET -n $NAMESPACE -o jsonpath='{.status.replicas}')
MIN=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
MAX=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
TARGET_CPU=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.metrics[0].resource.target.averageUtilization}' 2>/dev/null || echo "N/A")

echo "Replicas actuales: $CURRENT"
echo "Min replicas: $MIN"
echo "Max replicas: $MAX"
echo "Target CPU: $TARGET_CPU%"

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "FIN DEL DIAGNÓSTICO"
echo "═══════════════════════════════════════════════════════════════"
```

**Uso:**

```bash
chmod +x hpa-diagnostic.sh
./hpa-diagnostic.sh my-app-hpa production
```

---

# 8. RUNBOOKS

## 8.1 Runbook: HPA Alcanza maxReplicas

```markdown
# Alert: HPAAtMaxReplicas

## Descripción
HPA ha alcanzado el número máximo de replicas permitidas durante más de 5 minutos.

## Impacto
- La aplicación puede estar rechazando conexiones
- El sistema ha llegado a su límite de escalado
- Posible degradación del servicio

## Causa Raíz Probable
1. Tráfico genuinamente alto
2. maxReplicas configurado demasiado bajo
3. Memory leak o cpu leak en la aplicación
4. Servicio downstream degradado (DB, API externa)

## Diagnóstico Inmediato (5 min)

### Step 1: Confirmar la alerta
\`\`\`bash
kubectl get hpa <name> -n <namespace>
# Verifica que REPLICAS == MAXPODS
\`\`\`

### Step 2: Verificar tráfico real
\`\`\`bash
# Desde logs de aplicación
kubectl logs <pod-name> -n <namespace> | grep "request_rate" | tail -5

# Desde Prometheus
# rate(http_requests_total[5m])
\`\`\`

### Step 3: Revisar estado de pods
\`\`\`bash
kubectl top pods -n <namespace> -l app=<app>
# CPU y memory actual
\`\`\`

### Step 4: Revisar eventos
\`\`\`bash
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
# Buscar errores de escalado
\`\`\`

## Resolución

### Opción 1: Aumento Temporal (5 min)
Para evitar más degradación mientras investigas:

\`\`\`bash
kubectl patch hpa <name> -n <namespace> -p '{"spec":{"maxReplicas":200}}'

# Esperar a que pods se estabilicen
kubectl get hpa -n <namespace> --watch
\`\`\`

### Opción 2: Optimización de Aplicación (1-2 horas)
1. **Profiling de CPU:**
   \`\`\`bash
   kubectl exec <pod> -n <namespace> -- go tool pprof http://localhost:6060/debug/pprof/profile
   # Ver qué función consume CPU
   \`\`\`

2. **Revisar DB queries:**
   \`\`\`bash
   kubectl logs <pod> | grep "slow query" | head -10
   \`\`\`

3. **Implementar caching:**
   - Redis para resultados frecuentes
   - HTTP caching headers
   - Application-level caching

4. **Optimizar algoritmos:**
   - Reducir complejidad O(n²) a O(n log n)
   - Usar índices en BD

### Opción 3: Escalar Infraestructura
Si es problema de capacidad de nodos:

\`\`\`bash
# Verificar si hay pods Pending
kubectl get pods -n <namespace> | grep Pending

# Si hay Pending: Cluster Autoscaler escalará nodos
# Verificar nodos
kubectl get nodes
kubectl top nodes
\`\`\`

## Validación de Fix

- [ ] Replicas bajan de maxReplicas
- [ ] Tráfico se distribuye correctamente
- [ ] P95 latency dentro de SLA
- [ ] CPU/Memory utilization < target
- [ ] Sin nuevas alertas en 1 hora

## Escalación
Si no puedes resolver:
1. Contacta al Platform Team
2. Prepara logs y métricas de Prometheus
3. Documenta cambios temporales realizados

## Referencias
- Runbook: https://wiki.company.com/hpa-at-max
- Dashboard: https://grafana.company.com/d/hpa-debug
```

## 8.2 Runbook: HPA No Escala (Sin Métricas)

```markdown
# Troubleshooting: HPA sin escalar (FailedGetResourceMetric)

## Síntoma Principal
- `kubectl get hpa` muestra "unknown" en columna TARGETS
- Evento: `FailedGetResourceMetric`

## Checklist Diagnóstico Rápido (2 min)

\`\`\`bash
# 1. ¿Existe HPA?
kubectl get hpa <name> -n <namespace>

# 2. ¿Existe Metrics Server?
kubectl get deployment -n kube-system metrics-server

# 3. ¿Deployment tiene requests?
kubectl get deployment <name> -n <namespace> -o json | \
  jq '.spec.template.spec.containers[] | {name, resources}'

# 4. ¿Pod está corriendo (no Pending)?
kubectl get pods -n <namespace> | grep <deployment-prefix>

# 5. ¿Hay métricas en API?
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes | jq '.items[0]'
\`\`\`

## Soluciones por Diagnóstico

### Caso 1: Metrics Server no existe

\`\`\`bash
# Verificar
kubectl get deployment metrics-server -n kube-system
# Output: Error from server (NotFound)

# Solución
kubectl apply -f \
  https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Validar
kubectl wait --for=condition=available --timeout=300s \
  deployment/metrics-server -n kube-system
\`\`\`

### Caso 2: Pod sin requests

\`\`\`bash
# Verificar
kubectl get deployment <name> -o yaml | grep -A5 "resources:"
# Si está vacío = PROBLEMA

# Solución 1: Editar deployment
kubectl set resources deployment <name> \
  --requests=cpu=100m,memory=128Mi \
  --limits=cpu=500m,memory=512Mi

# Solución 2: Edit YAML
kubectl edit deployment <name>
# Agregar:
# resources:
#   requests:
#     cpu: 100m
#     memory: 128Mi
#   limits:
#     cpu: 500m
#     memory: 512Mi
\`\`\`

### Caso 3: Pod Pending (muy nuevo)

\`\`\`bash
# Es NORMAL si el pod acaba de crearse

# Esperar
sleep 120  # 2 minutos

# Reintentarq
kubectl get hpa <name> -n <namespace>
# Debería mostra métricas ahora
\`\`\`

### Caso 4: Metrics Server en CrashLoop

\`\`\`bash
# Verificar estado
kubectl get pod -n kube-system -l k8s-app=metrics-server

# Ver logs
kubectl logs -n kube-system -l k8s-app=metrics-server

# Soluciones comunes:
# - Verificar RBAC
# - Verificar que API es accesible
# - Reinstalar
kubectl delete deployment metrics-server -n kube-system
kubectl apply -f ...components.yaml
\`\`\`

## Después del Fix

1. Esperar 2 minutos para que métricas se estabilicen
2. Verificar: `kubectl get hpa` muestra porcentajes
3. Generar carga para verificar escalado:
   \`\`\`bash
   kubectl run load-gen --image=busybox --rm -it --restart=Never -- \
     /bin/sh -c "while true; do wget -q -O- http://<service>; done"
   \`\`\`
4. Monitorear: `kubectl get hpa -w`
```

---

# 9. CASOS DE USO

## 9.1 API REST Stateless

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  
  minReplicas: 3          # Mínimo para HA
  maxReplicas: 50         # Límite por costo
  
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
  
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0    # Escalar rápido
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 5
        periodSeconds: 30
      selectPolicy: Max
    
    scaleDown:
      stabilizationWindowSeconds: 300  # Esperar 5 min
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

## 9.2 Batch Job Worker

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: batch-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: batch-worker
  
  minReplicas: 1          # Puede ser 1 en batch
  maxReplicas: 100
  
  metrics:
  # Escalar basado en profundidad de cola
  - type: Pods
    pods:
      metric:
        name: job_queue_depth
        selector:
          matchLabels:
            queue: "process-jobs"
      target:
        type: AverageValue
        averageValue: "30"  # 30 jobs por worker
  
  # Fallback a CPU
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 200        # Duplicar si cola crece
        periodSeconds: 30
    
    scaleDown:
      stabilizationWindowSeconds: 600
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

## 9.3 Cache Layer (Redis)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: redis-cache-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: redis-cache
  
  minReplicas: 3
  maxReplicas: 20
  
  metrics:
  # Escalar basado en memoria usada
  - type: Pods
    pods:
      metric:
        name: redis_memory_used_bytes
        selector:
          matchLabels:
            app: redis
      target:
        type: AverageValue
        averageValue: "2Gi"   # 2GB por instancia
  
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 65
```

## 9.4 ML Inference Service

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-inference
  
  minReplicas: 2
  maxReplicas: 30
  
  metrics:
  # CPU es crítico para inference
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60   # Más bajo para latencia
  
  # Cola de requests pendientes
  - type: Pods
    pods:
      metric:
        name: inference_queue_length
      target:
        type: AverageValue
        averageValue: "5"   # 5 inferencias en queue máximo
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15    # Más agresivo
      selectPolicy: Max
    
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

---

# 10. COST OPTIMIZATION

## 10.1 Right-Sizing Strategy

```yaml
# 1. Profiling Job para medir uso real
apiVersion: batch/v1
kind: Job
metadata:
  name: resource-profiler
spec:
  template:
    spec:
      containers:
      - name: profiler
        image: your-profiling-tool:v1
        env:
        - name: DURATION_MINUTES
          value: "60"
        - name: SAMPLE_INTERVAL
          value: "10"  # Cada 10 segundos
        volumeMounts:
        - name: output
          mountPath: /output
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
      
      volumes:
      - name: output
        emptyDir: {}
      
      restartPolicy: Never
```

**Fórmula de Right-Sizing:**

```
requests.cpu = P50_usage × 1.2 (20% buffer)
limits.cpu = P95_usage × 1.5 (50% buffer)

requests.memory = P50_usage × 1.2
limits.memory = P95_usage × 1.5

Ejemplo:
P50 CPU: 80m  → requests = 96m ≈ 100m
P95 CPU: 120m → limits = 180m
```

## 10.2 Cost Attribution

```promql
# Cálculo de costo por deployment

# CPU cost
sum(rate(container_cpu_usage_seconds_total{pod=~"app-.*"}[5m])) 
by (deployment) 
* 3600 
* 0.025  # $/hour

# Memory cost
sum(container_memory_working_set_bytes{pod=~"app-.*"}) 
by (deployment) 
/ 1024 / 1024 / 1024 
* 0.0015  # $/GB/hour

# Total
(cpu_cost + memory_cost) * 24  # diario
```

## 10.3 Budget Alerts

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cost-budget-alerts
spec:
  groups:
  - name: cost.alerts
    rules:
    - alert: DailyComputeBudgetExceeded
      expr: |
        (sum(rate(container_cpu_usage_seconds_total[5m])) * 3.6 * 0.025 +
         sum(container_memory_working_set_bytes) / 1024^3 * 0.0015) * 24 
        > 10000  # $10k presupuesto diario
      for: 30m
      severity: warning
      annotations:
        summary: "Gasto diario excede presupuesto"
        cost: "${{ $value }}"
```

---

# 11. TESTING Y VALIDACIÓN

## 11.1 Load Testing Framework

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: hpa-load-test
spec:
  template:
    spec:
      containers:
      - name: k6-load-test
        image: grafana/k6:latest
        volumeMounts:
        - name: test-script
          mountPath: /scripts
        env:
        - name: TARGET_URL
          value: "http://my-app:8080"
        - name: DURATION
          value: "10m"
        command:
        - k6
        - run
        - --vus=50
        - --duration=10m
        - /scripts/load-test.js
      
      volumes:
      - name: test-script
        configMap:
          name: load-test-script
      
      restartPolicy: Never
  
  backoffLimit: 1
```

## 11.2 Test Script (k6)

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep, group } from 'k6';

const TARGET = __ENV.TARGET_URL || 'http://localhost:8080';

export const options = {
  stages: [
    { duration: '2m', target: 20 },      // Ramp-up
    { duration: '5m', target: 50 },      // Steady (peak)
    { duration: '2m', target: 0 },       // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],    // 95% < 500ms
    http_req_failed: ['rate<0.1'],       // < 10% fallos
  },
};

export default function () {
  group('API Requests', function () {
    const res = http.get(`${TARGET}/api/endpoint`);
    
    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
      'body has correct format': (r) => r.headers['Content-Type'].includes('application/json'),
    });
  });
  
  sleep(1);
}
```

## 11.3 Script de Validación Automatizada

```bash
#!/bin/bash
# validate-hpa.sh

set -e

DEPLOYMENT="$1"
NAMESPACE="${2:-default}"
HPA_NAME="$3"

echo "🔍 Validando HPA para: $DEPLOYMENT"

# 1. Verificar que HPA existe
if ! kubectl get hpa $HPA_NAME -n $NAMESPACE &>/dev/null; then
  echo "❌ FAIL: HPA no encontrado"
  exit 1
fi

# 2. Verificar minReplicas >= 2
MIN=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
if [ "$MIN" -lt 2 ]; then
  echo "❌ FAIL: minReplicas ($MIN) < 2"
  exit 1
fi

# 3. Verificar maxReplicas <= 100
MAX=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.maxReplicas}')
if [ "$MAX" -gt 100 ]; then
  echo "❌ FAIL: maxReplicas ($MAX) > 100"
  exit 1
fi

# 4. Verificar que Deployment tiene requests/limits
if ! kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o json | \
  jq -e '.spec.template.spec.containers[] | select(.resources.requests.cpu == null)' | grep -q .; then
  echo "❌ FAIL: Container sin requests.cpu"
  exit 1
fi

echo "✅ Validaciones estáticas pasaron"

# 5. Generar carga y validar escalado
echo "📊 Iniciando prueba de carga..."

# Run load in background
kubectl run load-gen-$RANDOM --image=busybox --rm --restart=Never -- \
  /bin/sh -c "for i in {1..1000}; do wget -q -O- http://$DEPLOYMENT; done" &

LOAD_PID=$!

# Monitor replicas
echo "⏳ Esperando que HPA escale..."
INITIAL_REPLICAS=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.replicas}')
SCALED=false

for i in {1..60}; do
  CURRENT=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.replicas}')
  
  if [ "$CURRENT" -gt "$INITIAL_REPLICAS" ]; then
    echo "✅ PASS: HPA escaló de $INITIAL_REPLICAS a $CURRENT replicas"
    SCALED=true
    break
  fi
  
  echo "  Intento $i/60: $CURRENT replicas"
  sleep 5
done

# Cleanup
wait $LOAD_PID 2>/dev/null || true

if [ "$SCALED" = false ]; then
  echo "❌ FAIL: HPA no escaló después de 5 minutos"
  exit 1
fi

echo -e "\n🎉 TODAS LAS VALIDACIONES PASARON"
exit 0
```

---

# 12. INTEGRACIÓN CON CLUSTER AUTOSCALING

## 12.1 Arquitectura de Escalado en Capas

```
┌─────────────────────────────────────────────┐
│         APPLICATION LAYER (HPA)             │
│  Escala: Pods (dentro de capacidad nodo)    │
│  Métrica: CPU, Memory, Custom               │
│  Min: 2 → Max: 50 pods                      │
└────────────────┬────────────────────────────┘
                 │ Pods se vuelven Pending
                 │ (no cabe en nodos)
┌────────────────▼────────────────────────────┐
│      NODE LAYER (Cluster Autoscaler)        │
│  Escala: Nodos (cuando hay Pods Pending)    │
│  Min: 3 → Max: 100 nodos                    │
└─────────────────────────────────────────────┘
```

## 12.2 Configuración Coordinada

```yaml
# HPA config (application level)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 50      # ← Límite de pods
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---
# Cluster Autoscaler config (infrastructure level)
# Se configura típicamente como flags en la gráfica Helm
# o como Karpenter (recomendado para K8s modernos)
# Parámetros clave:
# - min-total-nodes: 3
# - max-total-nodes: 100
# - scale-down-enabled: true
# - scale-down-delay-after-add: 10m
# - skip-nodes-with-local-storage: false

---
# Priority Class para guiar el escalado
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-workload
value: 1000
globalDefault: false
description: "Apps críticas que disparan escalado de nodos"

---
# Pod usando PriorityClass
apiVersion: v1
kind: Pod
metadata:
  name: critical-app
spec:
  priorityClassName: high-priority-workload
  containers:
  - name: app
    image: my-app:v1
```

## 12.3 Prevención de Ciclos Infinitos

```yaml
# ✗ PELIGROSO: Sin límites duros
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bad-hpa
spec:
  maxReplicas: 1000     # ← Demasiado alto
  # Puede crear ciclo infinito con CA

---
# ✓ CORRECTO: Con límites y comportamiento controlado
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: good-hpa
spec:
  minReplicas: 2
  maxReplicas: 50       # ← Límite DURO
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Pods
        value: 4        # ← Máximo 4 nuevos cada 30s
        periodSeconds: 30
      - type: Percent
        value: 100
        periodSeconds: 30
      selectPolicy: Max # Elige el que más agrega
```

---

# 13. CHECKLIST DE IMPLEMENTACIÓN

## 13.1 Pre-Implementación (Semana 1)

```
PLANNING
☐ Definir política organizacional de HPA
☐ Documentar estándares (min/max replicas, targets)
☐ Identificar aplicaciones que usan HPA
☐ Reservar recursos para testing

PREPARACIÓN
☐ Instalar Metrics Server
☐ Verificar que proporciona métricas
☐ Revisar RBAC para HPA Controller
☐ Preparar templates Helm
```

## 13.2 Implementación (Semana 2-3)

```
DEVELOPMENT
☐ Crear Helm chart con HPA base
☐ Agregar ejemplos por caso de uso
☐ Crear admission webhook de validación
☐ Definir alertas en Prometheus

TESTING
☐ Probar HPA en dev/staging
☐ Validar escalado manual
☐ Realizar load testing
☐ Revisar logs y eventos
```

## 13.3 Despliegue (Semana 4)

```
ROLLOUT
☐ Desplegar HPA en 5-10% apps
☐ Monitorear eventos y alertas
☐ Validar que replica counts son correctos
☐ Recolectar feedback de equipos

SCALE
☐ Extender a más aplicaciones
☐ Documentar patrones comunes
☐ Ajustar thresholds basado en observaciones
☐ Optimizar targets de CPU/Memory
```

## 13.4 Operación Continua

```
MONTHLY
☐ Revisar HPAs con maxReplicas alto
☐ Analizar costo vs beneficio
☐ Actualizar policies si es necesario

QUARTERLY
☐ Revisar right-sizing de requests/limits
☐ Comparar uso real vs configurado
☐ Optimizar cooldowns
☐ Renovar runbooks

ONGOING
☐ Responder a alertas
☐ Capacitar nuevos teams
☐ Mejorar observabilidad
☐ Iterar en políticas
```

---

# REFERENCIA RÁPIDA

## Comandos Esenciales

```bash
# Ver HPAs
kubectl get hpa -A
kubectl describe hpa <name> -n <namespace>
kubectl get hpa -o wide

# Monitoreo
kubectl get hpa -w
kubectl top pods
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Diagnóstico
kubectl logs -n kube-system -l k8s-app=metrics-server
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes

# Validación
kubectl auth can-i update deployment --as=system:serviceaccount:kube-system:horizontal-pod-autoscaler
```

## Fórmulas Clave

```
Utilización (%) = (Uso Real / Requests) × 100

desiredReplicas = ceil(
    (sumMetricActual / sumMetricTarget) × replicasActuales
)

requests = P50_uso × 1.2
limits = P95_uso × 1.5
```

## Tabla de Decisiones

| Síntoma | Causa | Solución |
|---------|-------|----------|
| "unknown" en TARGETS | Sin métricas | Instalar MS, agregar requests |
| No escala arriba | maxReplicas bajo | Aumentar max o optimizar |
| Oscila constantemente | stabilizationWindow bajo | Aumentar a 300s |
| Costo muy alto | Over-provisioning | Right-sizing, HPA agresivo |
| Pods Pending | Sin espacio en nodos | Cluster Autoscaler escala |
| FailedRescale | RBAC | Revisar permisos |

---

# CONCLUSIÓN

Horizontal Pod Autoscaling es una **herramienta fundamental** para:
- ✅ Mejorar eficiencia de recursos
- ✅ Reducir costos de infraestructura
- ✅ Responder automáticamente a cambios de carga
- ✅ Garantizar disponibilidad sin over-provisioning

**Key Takeaway:** HPA funciona mejor cuando está **bien observado**, **correctamente configurado** y **coordinado** con otras capas de escalado (Cluster Autoscaler, VPA).

Para más información:
- Documentación oficial: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- Spec API: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/#horizontalpodautoscaler-v2-autoscaling
- KEDA (métricas externas): https://keda.sh

---

**Documento compilado:** Versión 2.0 (2026)  
**Actualización anterior:** Inclusión de eventos, troubleshooting, runbooks  
**Próximas mejoras:** Integración con Karpenter, KEDA avanzado