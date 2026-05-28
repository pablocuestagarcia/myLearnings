# HPA Best Practices para Staff Platform Engineers

## ÍNDICE EJECUTIVO

Como Staff Platform Engineer, tu responsabilidad es:
- Definir **estándares organizacionales** para HPA
- Implementar **observabilidad y gobernanza**
- Garantizar **escalabilidad segura y eficiente**
- Capacitar y habilitar a los equipos de desarrollo

---

## 1. GOBERNANZA Y ESTANDARIZACIÓN

### 1.1 Política de HPA Organizacional

```yaml
# kube-system/hpa-policy-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hpa-organization-policy
  namespace: kube-system
data:
  min_replicas: "2"  # Nunca menos de 2 (HA)
  max_replicas_limit: "100"  # Tope máximo
  cpu_target_default: "70"  # 70% es estándar
  memory_target_default: "75"
  scale_down_stabilization: "300"  # 5 minutos mínimo
  scale_up_stabilization: "0"  # Escalar rápido
  default_namespace: "default"
  requires_monitoring: "true"
```

### 1.2 Requisistos Obligatorios para HPA

**Checklist para QA/Validación:**

```
✓ Deployment/StatefulSet con requests/limits DEFINIDOS
  └─ requests.cpu >= 100m
  └─ limits.cpu >= requests.cpu × 2
  └─ memory configurado
  
✓ HPA configurado con:
  └─ minReplicas >= 2 (alta disponibilidad)
  └─ maxReplicas <= 100 (protección de costos)
  └─ metrics >= 2 (CPU + otra)
  
✓ Pod Disruption Budget (PDB) configurado
  └─ minAvailable >= 1 o maxUnavailable <= 50%
  
✓ Health checks (liveness + readiness)
  └─ readinessProbe para escalar correctamente
  
✓ Alertas configuradas
  └─ Alerta cuando HPA está en maxReplicas
  └─ Alerta cuando HPA falla
```

### 1.3 Template Estándar para Equipos

```yaml
# helm/charts/app-template/values.yaml
replicaCount: 2

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 75

podDisruptionBudget:
  enabled: true
  minAvailable: 1

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 2. OBSERVABILIDAD ENTERPRISE

### 2.1 Métricas a Exponer

**En tu Prometheus/Grafana, registra:**

```yaml
# Custom metrics que debes monitorear
ServiceMonitor:
  - name: hpa_scaling_events
    labels:
      deployment: "{{ deployment }}"
      action: "scale_up|scale_down"
      timestamp: "{{ event_time }}"
      previous_replicas: "{{ old_count }}"
      new_replicas: "{{ new_count }}"
      reason: "{{ metric_name }}"
      
  - name: hpa_target_utilization
    labels:
      deployment: "{{ deployment }}"
      metric: "cpu|memory"
      current: "{{ actual_usage }}"
      target: "{{ target_percentage }}"
      
  - name: hpa_scaling_failures
    labels:
      deployment: "{{ deployment }}"
      error: "{{ error_reason }}"
```

### 2.2 Queries Prometheus Recomendadas

```promql
# 1. Replicas actuales vs máximas
(kube_deployment_status_replicas{deployment=~".*"} / 
 kube_deployment_spec_replicas_max{deployment=~".*"}) * 100

# 2. Tasa de escalado (cambios por hora)
increase(kube_deployment_status_replicas[1h])

# 3. HPA alcanzando límites
kube_deployment_status_replicas == 
kube_deployment_spec_replicas_max

# 4. Latencia de escalado
histogram_quantile(0.95, 
  rate(hpa_scaling_latency_seconds_bucket[5m]))

# 5. Estabilidad de replicas
stddev(rate(kube_deployment_status_replicas[5m]))
```

### 2.3 Alertas Críticas (PrometheusRule)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: hpa-alerts
spec:
  groups:
  - name: hpa.rules
    interval: 30s
    rules:
    
    # ALERTA 1: HPA alcanza maxReplicas
    - alert: HPAMaxReplicasReached
      expr: |
        kube_deployment_status_replicas == kube_deployment_spec_replicas_max
      for: 5m
      severity: warning
      annotations:
        summary: "{{ $labels.deployment }} está en máximo ({{ $value }} replicas)"
        description: "Aumentar maxReplicas o revisar la app"
        runbook: "https://wiki.company.com/hpa-max-replicas"
    
    # ALERTA 2: HPA no logra escalar
    - alert: HPAScalingFailure
      expr: |
        increase(hpa_scaling_failures_total[10m]) > 0
      severity: critical
      annotations:
        summary: "HPA en {{ $labels.deployment }} no puede escalar"
        runbook: "https://wiki.company.com/hpa-scaling-failure"
    
    # ALERTA 3: Sin métricas disponibles
    - alert: HPAMissingMetrics
      expr: |
        absent(container_cpu_usage_seconds_total{pod=~".*"}) == 1
      for: 2m
      severity: critical
      annotations:
        summary: "Metrics Server no está reportando CPU"
    
    # ALERTA 4: Comportamiento oscilatorio
    - alert: HPAFlapping
      expr: |
        stddev(increase(kube_deployment_status_replicas[1m])) > 2
      for: 10m
      severity: warning
      annotations:
        summary: "{{ $labels.deployment }} oscila entre replicas"
        description: "Ajustar stabilizationWindow o target"
```

### 2.4 Dashboard Grafana Template

```json
{
  "dashboard": {
    "title": "HPA Monitoring - Organization Wide",
    "panels": [
      {
        "title": "Replicas Actuales vs Target",
        "targets": [
          {
            "expr": "kube_deployment_status_replicas{namespace=~\"$namespace\"}"
          }
        ]
      },
      {
        "title": "CPU Utilization vs Target",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[1m]) * 100"
          }
        ]
      },
      {
        "title": "Scaling Events Timeline",
        "targets": [
          {
            "expr": "increase(hpa_scaling_events_total[1h])"
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
      }
    ]
  }
}
```

---

## 3. INTEGRACIÓN CON CLUSTER AUTOSCALING

### 3.1 Modelo de Escalado en Capas

```
┌─────────────────────────────────────────────────┐
│           APPLICATION LAYER (HPA)               │
│  Escala Pods basado en: CPU, Memory, Custom     │
│  Min: 2  →  Max: 100                            │
└──────────────────┬──────────────────────────────┘
                   │ Necesita más recursos en nodos
┌──────────────────▼──────────────────────────────┐
│         NODE LAYER (Cluster Autoscaling)        │
│  Escala Nodos cuando Pods están pendientes      │
│  Min: 3  →  Max: 100                            │
└─────────────────────────────────────────────────┘
```

### 3.2 Configuración Coordinada

```yaml
# HPA - Escalado de Pods
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-app
  minReplicas: 2
  maxReplicas: 50  # Máximo de pods
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---
# Cluster Autoscaler - Escalado de Nodos
# (Generalmente configurado en valores de Helm del CA)
# Parámetros clave:
# - min-total-nodes: 3
# - max-total-nodes: 100
# - scale-down-enabled: true
# - scale-down-delay-after-add: 10m
# - expander: priority (usa PriorityClasses)

---
# Pod Priority para que CA escale nodos correctamente
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-app
value: 1000
globalDefault: false
description: "Apps críticas que disparan escalado de nodos"

---
# Especificar en el Pod
apiVersion: v1
kind: Pod
spec:
  priorityClassName: high-priority-app
```

### 3.3 Prevención de Ciclos Infinitos

```yaml
# CORRECTO: Proteger que HPA no dispare escalado infinito de nodos
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-app
  minReplicas: 2
  maxReplicas: 50  # ← Límite DURO
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
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4  # ← Máximo 4 pods nuevos cada 30s
        periodSeconds: 30
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

---

## 4. COST OPTIMIZATION

### 4.1 Right-Sizing Strategy

```yaml
# Profiling Script para encontrar valores correctos
apiVersion: batch/v1
kind: Job
metadata:
  name: resource-profiling-job
spec:
  template:
    spec:
      containers:
      - name: profiler
        image: your-profiling-tool
        env:
        - name: DURATION_MINUTES
          value: "60"
        - name: CAPTURE_PERCENTILE
          value: "95"  # P95 para requests, P99 para limits
      restartPolicy: Never
```

**Fórmula Recomendada:**

```
requests.cpu = P50 usage × 1.2 (20% buffer)
limits.cpu = P95 usage × 1.5 (50% buffer)

requests.memory = P50 usage × 1.2
limits.memory = P95 usage × 1.5
```

### 4.2 Cost Attribution per HPA

```promql
# Calcular costo actual por deployment con HPA
sum(rate(container_cpu_usage_seconds_total{pod=~"app-.*"}[5m])) 
by (deployment) * 3600 * $cpu_cost_per_hour

sum(container_memory_working_set_bytes{pod=~"app-.*"}) 
by (deployment) / 1024 / 1024 / 1024 * $memory_cost_per_gb_hour
```

### 4.3 Budget Alerts

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cost-alerts
spec:
  groups:
  - name: cost.rules
    rules:
    - alert: DailyComputeCostExceeded
      expr: |
        (sum(rate(container_cpu_usage_seconds_total[5m]) * $cpu_hourly_cost 
             + container_memory_working_set_bytes / 1024^3 * $mem_hourly_cost) * 24) > $daily_budget
      for: 30m
      annotations:
        summary: "Gasto diario de compute excede presupuesto"
```

---

## 5. SEGURIDAD Y COMPLIANCE

### 5.1 RBAC para HPA

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: hpa-manager
rules:
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dev-team-hpa-manager
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: hpa-manager
subjects:
- kind: Group
  name: "dev-team@company.com"
  apiGroup: rbac.authorization.k8s.io
```

### 5.2 Validación de Configuración (Admission Controller)

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: hpa-validator
webhooks:
- name: hpa-validation.platform.company.com
  clientConfig:
    service:
      name: hpa-validator
      namespace: kube-system
      path: "/validate"
    caBundle: LS0tLS1CRU...
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["autoscaling"]
    apiVersions: ["v2"]
    resources: ["horizontalpodautoscalers"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  timeoutSeconds: 5
```

**Lógica del Webhook:**

```python
def validate_hpa(admission_review):
    hpa = admission_review['request']['object']
    errors = []
    
    # Validaciones obligatorias
    if hpa['spec']['minReplicas'] < 2:
        errors.append("minReplicas debe ser >= 2")
    
    if hpa['spec']['maxReplicas'] > 100:
        errors.append("maxReplicas no puede exceder 100")
    
    if len(hpa['spec'].get('metrics', [])) < 2:
        errors.append("Se requieren al menos 2 métricas")
    
    # Verificar que el Deployment tiene requests/limits
    deployment = get_deployment(hpa['spec']['scaleTargetRef'])
    for container in deployment['spec']['template']['spec']['containers']:
        if not container.get('resources', {}).get('requests', {}).get('cpu'):
            errors.append(f"Container {container['name']} sin requests.cpu")
    
    if errors:
        return deny(errors)
    else:
        return allow()
```

---

## 6. TESTING Y VALIDACIÓN

### 6.1 Load Testing Framework

```yaml
# Usando k6 o Locust
apiVersion: batch/v1
kind: Job
metadata:
  name: hpa-load-test
spec:
  template:
    spec:
      containers:
      - name: load-generator
        image: grafana/k6:latest
        volumeMounts:
        - name: test-script
          mountPath: /scripts
        env:
        - name: TARGET_DEPLOYMENT
          value: "my-app"
        - name: DURATION
          value: "10m"
        - name: RAMP_UP_TIME
          value: "2m"
        command:
        - k6
        - run
        - --vus=100
        - --duration=10m
        - /scripts/load-test.js
      volumes:
      - name: test-script
        configMap:
          name: load-test-script
      restartPolicy: Never
```

### 6.2 Test Scenarios Automatizados

```javascript
// load-test.js - k6 test script
import http from 'k6/http';
import { check, sleep } from 'k6';

const TARGET = __ENV.TARGET_DEPLOYMENT || 'my-app';
const NAMESPACE = __ENV.NAMESPACE || 'default';

export const options = {
  stages: [
    { duration: '2m', target: 100 },    // Ramp-up
    { duration: '5m', target: 100 },    // Steady
    { duration: '2m', target: 50 },     // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% bajo 500ms
    http_req_failed: ['rate<0.1'],      // <10% fallos
  },
};

export default function () {
  const res = http.get(`http://${TARGET}/api/endpoint`);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

### 6.3 Validación de Escalado

```bash
#!/bin/bash
# hpa-validation.sh

set -e

DEPLOYMENT="my-app"
NAMESPACE="default"
HPA_NAME="my-app-hpa"
THRESHOLD_REPLICAS=5

echo "🔍 Validando HPA..."

# 1. Verificar que HPA existe
kubectl get hpa $HPA_NAME -n $NAMESPACE

# 2. Verificar minReplicas >= 2
MIN=$(kubectl get hpa $HPA_NAME -n $NAMESPACE -o jsonpath='{.spec.minReplicas}')
if [ "$MIN" -lt 2 ]; then
  echo "❌ FAIL: minReplicas ($MIN) < 2"
  exit 1
fi

# 3. Verificar que Deployment tiene requests/limits
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o json | \
  jq -e '.spec.template.spec.containers[] | select(.resources.requests.cpu == null)' && \
  { echo "❌ FAIL: Container sin requests.cpu"; exit 1; } || true

# 4. Generar carga y validar escalado
echo "📊 Generando carga..."
kubectl run load-gen --image=busybox --rm -it --restart=Never -- \
  /bin/sh -c "for i in {1..1000}; do wget -q -O- http://$DEPLOYMENT; done" &

# 5. Monitorear replicas
echo "⏳ Esperando que HPA escale..."
for i in {1..60}; do
  REPLICAS=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.replicas}')
  echo "Intento $i: $REPLICAS replicas"
  
  if [ "$REPLICAS" -gt "$THRESHOLD_REPLICAS" ]; then
    echo "✅ PASS: HPA escaló exitosamente a $REPLICAS replicas"
    exit 0
  fi
  
  sleep 5
done

echo "❌ FAIL: HPA no escaló después de 5 minutos"
exit 1
```

---

## 7. RUNBOOKS Y DOCUMENTACIÓN

### 7.1 Runbook: "HPA alcanza maxReplicas"

```markdown
# Alerta: HPA Alcanza máximo de Replicas

## Síntomas
- AlertManager dispara: `HPAMaxReplicasReached`
- Dashboard muestra deployment con replicas == maxReplicas por > 5 minutos

## Causas Posibles
1. Traffic genuino > capacidad del sistema
2. maxReplicas muy bajo
3. Application leak de memoria / connections
4. Downstream service degradado

## Diagnóstico

### Paso 1: Verificar tráfico real
\`\`\`bash
kubectl logs deployment/my-app -n prod --tail=100 | grep "request_rate"
# O desde Prometheus:
# rate(http_requests_total[5m])
\`\`\`

### Paso 2: Revisar estado de la app
\`\`\`bash
kubectl top pods -l app=my-app -n prod
kubectl describe deployment my-app -n prod
\`\`\`

### Paso 3: Verificar servicios downstream
\`\`\`bash
# Bases de datos, colas, APIs externas
kubectl logs -l app=my-app -n prod | grep "error" | head -20
\`\`\`

## Resolución

### Opción 1: Aumentar maxReplicas (temporal)
\`\`\`bash
kubectl patch hpa my-app-hpa -n prod -p '{"spec":{"maxReplicas":200}}'
\`\`\`

### Opción 2: Optimizar aplicación (permanente)
- Profiling de CPU/Memoria
- Optimizar queries a BD
- Implementar caching
- Mejorar eficiencia de algoritmos

### Opción 3: Escalar nodos
\`\`\`bash
# Si no hay espacio en nodos
kubectl patch daemonset aws-node -n kube-system --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/nodeSelector", "value":{"karpenter.sh/capacity-type":"spot"}}]'
\`\`\`

## Validación de Fix
- [ ] Replicas bajan de maxReplicas
- [ ] P95 latency < SLA
- [ ] CPU utilization < target
- [ ] Alerta no dispara por 1 hora
```

### 7.2 Runbook: "HPA no escala (sin métricas)"

```markdown
# Troubleshooting: HPA No Escala

## Checklist Rápido
\`\`\`bash
# 1. ¿Existe HPA?
kubectl get hpa my-app-hpa

# 2. ¿Existen métricas?
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/default/pods | jq '.items[0]'

# 3. ¿Metrics Server está corriendo?
kubectl get pod -n kube-system -l k8s-app=metrics-server

# 4. ¿Tiene el pod requests?
kubectl get pod my-app-xyz -o yaml | grep -A5 "resources:"

# 5. ¿El pod está corriendo (no pending)?
kubectl get pod my-app-xyz -o wide
\`\`\`

## Solución por síntoma

### Síntoma: "unknown" en target
**Causa:** Sin métrica disponible
**Solución:**
\`\`\`bash
# Esperar 1-2 minutos después de crear deployment
sleep 120
kubectl get hpa -w
\`\`\`

### Síntoma: Deployment sin requests
**Solución:**
\`\`\`yaml
# Agregar a deployment:
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
\`\`\`

### Síntoma: Metrics Server en CrashLoop
\`\`\`bash
# Revisar logs
kubectl logs -n kube-system -l k8s-app=metrics-server
# Reinstalar
kubectl delete -n kube-system deployment metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
\`\`\`
```

---

## 8. CAPACITACIÓN Y ENABLEMENT

### 8.1 Checklist para Onboarding de Equipos

```
PRE-REQUERIMIENTOS
☐ Kubeconfig configurado
☐ Acceso a namespace asignado
☐ Herramientas instaladas: kubectl, helm, k6
☐ Entender requests/limits (5 min)

HANDS-ON
☐ Crear Deployment con requests/limits (10 min)
☐ Aplicar HPA simple (10 min)
☐ Ver escalado en acción con load testing (15 min)
☐ Revisar métricas en Prometheus (10 min)
☐ Crear alerta para HPA (10 min)

VALIDACIÓN
☐ Quiz: ¿Qué pasa si minReplicas > maxReplicas?
☐ Ejercicio: Optimizar HPA existente
☐ Revisión de pares: Pull Request con HPA

CERTIFICACIÓN
☐ Puede diseñar HPA para nueva app
☐ Puede troubleshoot HPA existente
☐ Conoce límites de cluster (max pods, nodos)
```

### 8.2 Ejemplos Comunes por Caso de Uso

```yaml
# ==== CASO 1: API REST ====
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 50
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

---
# ==== CASO 2: Batch Job ====
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: batch-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: batch-processor
  minReplicas: 1  # Puede ser 1 en batch
  maxReplicas: 100
  metrics:
  - type: Pods
    pods:
      metric:
        name: job_queue_depth
      target:
        type: AverageValue
        averageValue: "30"  # 30 jobs por pod

---
# ==== CASO 3: Cache Layer (Redis, Memcached) ====
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cache-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: redis
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: redis_memory_used_bytes
      target:
        type: AverageValue
        averageValue: "2G"  # 2GB por instancia
  
---
# ==== CASO 4: ML Inference Service ====
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-inference
  minReplicas: 2
  maxReplicas: 30
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Pods
    pods:
      metric:
        name: inference_queue_length
      target:
        type: AverageValue
        averageValue: "5"  # 5 inferencias pendientes máx
```

---

## 9. CHECKLIST DE IMPLEMENTACIÓN PARA STAFF

### Fase 1: Foundation (Semana 1-2)
- [ ] Instalar y configurar Metrics Server
- [ ] Definir política organizacional de HPA
- [ ] Crear admission webhook de validación
- [ ] Establecer naming conventions y tagging

### Fase 2: Observability (Semana 3-4)
- [ ] Implementar PrometheusRules para alertas
- [ ] Crear dashboards en Grafana
- [ ] Configurar logging de eventos de HPA
- [ ] Integración con ChatOps (Slack alerts)

### Fase 3: Automation (Semana 5-6)
- [ ] Crear Helm chart estándar con HPA
- [ ] Automatizar testing de HPA
- [ ] Implementar cost tracking
- [ ] Crear runbooks

### Fase 4: Enablement (Semana 7-8)
- [ ] Capacitación de equipos
- [ ] Code review de HPAs
- [ ] Documentación en wiki
- [ ] Office hours para Q&A

### Fase 5: Operación (Ongoing)
- [ ] Review mensual de HPAs
- [ ] Optimization basada en métricas
- [ ] Feedback loop con equipos
- [ ] Iteración en políticas

---

## 10. MÉTRICAS DE ÉXITO

```yaml
# KPIs para medir éxito de HPA en tu org
Metrics:
  HPA_adoption: 
    target: "80% of stateless deployments"
    current: "track in CMDB"
  
  scaling_accuracy:
    target: "HPA triggers only when needed"
    measure: "unnecessary_scale_events / total_events < 10%"
  
  cost_efficiency:
    target: "20% reduction in over-provisioning"
    measure: "Compare: previous fixed replicas vs HPA actual usage"
  
  mean_scale_time:
    target: "< 2 minutes from need to scaled"
    measure: "lag between metric change and replica change"
  
  incident_rate:
    target: "< 1 HPA-related incident per month"
    measure: "postmortems with root cause = HPA misconfiguration"

SLO:
  availability: 99.95%  # HPA debe ser transparent
  scaling_success_rate: 99%  # Escalados exitosos
```

---

## RESUMEN EJECUTIVO

### Lo Más Importante Como Staff Engineer

```
1️⃣ GOBERNANZA
   └─ Política clara, admission webhooks, templates estándar

2️⃣ OBSERVABILIDAD  
   └─ Alertas de maxReplicas, Prometheus rules, Grafana dashboards

3️⃣ COSTO
   └─ Right-sizing, budget alerts, cost attribution

4️⃣ CONFIABILIDAD
   └─ Testing automation, runbooks, rundown procedures

5️⃣ HABILITACIÓN
   └─ Documentación, onboarding, ejemplos por caso de uso

6️⃣ CONTINUOUS IMPROVEMENT
   └─ Métricas, feedback, iteración monthly
```

### Comandos Críticos que Todos Deben Saber

```bash
# Ver estado de HPA
kubectl get hpa -A
kubectl describe hpa <name>
kubectl get hpa -w

# Revisar métricas
kubectl top pods
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes

# Troubleshooting
kubectl logs -n kube-system -l k8s-app=metrics-server
kubectl get events -A --sort-by='.lastTimestamp'

# Testing
kubectl run load-gen --image=busybox --rm -it -- \
  /bin/sh -c "while true; do wget -q -O- http://service; done"
```