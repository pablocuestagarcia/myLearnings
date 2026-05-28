# Horizontal Pod Autoscaling (HPA) - Guía Completa

## 1. CONCEPTOS TEÓRICOS FUNDAMENTALES

### ¿Qué es HPA?

El **Horizontal Pod Autoscaling** es un mecanismo en Kubernetes que automáticamente escala el número de pods de una aplicación basándose en métricas observadas, como uso de CPU, memoria u otras métricas personalizadas.

### Diferencia: Escalado Horizontal vs Vertical

| Aspecto | Escalado Horizontal | Escalado Vertical |
|--------|-------------------|------------------|
| **Qué escala** | Número de pods | Recursos (CPU/Memoria) por pod |
| **Método** | HPA (Horizontal Pod Autoscaling) | VPA (Vertical Pod Autoscaling) |
| **Aplicación** | Distribuir carga entre múltiples instancias | Ajustar recursos de instancias individuales |
| **Ventajas** | Alta disponibilidad, mejor distribución | Menos complejidad operacional |

### Componentes de HPA

1. **Metrics Server**: Recopila métricas de recursos de los nodos
2. **HPA Controller**: Consulta métricas y decide cuándo escalar
3. **Deployment/StatefulSet**: La aplicación que se escalará
4. **Recurso HPA**: Define las reglas de escalado

---

## 2. ¿CÓMO FUNCIONA HPA?

### El Ciclo de Funcionamiento

```
┌─────────────────────────────────────────────────────────┐
│                    CICLO DE HPA                         │
├─────────────────────────────────────────────────────────┤
│ 1. Metrics Server recopila datos cada 15s               │
│ 2. HPA Controller consulta cada 15s (por defecto)       │
│ 3. Calcula: utilización actual vs. target               │
│ 4. Calcula: pods necesarios = ceil(actual/target)       │
│ 5. Compara con min/max replicas                         │
│ 6. Escala si es necesario                               │
│ 7. Espera cooldown (3 min escalada, 5 min reducción)   │
└─────────────────────────────────────────────────────────┘
```

### Fórmula de Cálculo

```
replicas_deseadas = ceil(
    (métrica_actual / métrica_target) × replicas_actuales
)
```

**Ejemplo:**
- Replicas actuales: 3
- CPU actual promedio: 80%
- CPU target: 50%
- Cálculo: ceil((80/50) × 3) = ceil(4.8) = 5 replicas

### Límites y Restricciones

- **minReplicas**: Número mínimo de pods (default: 1)
- **maxReplicas**: Número máximo de pods
- **targetCPUUtilizationPercentage**: % de CPU deseado (60% es común)
- **Scale-up cooldown**: 3 minutos (espera antes de aumentar nuevamente)
- **Scale-down cooldown**: 5 minutos (espera antes de reducir)

---

## 3. CONFIGURACIÓN PRÁCTICA

### Requisito Previo: Instalar Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verificar que está corriendo
kubectl get deployment metrics-server -n kube-system
```

### 3.1 HPA Simple basado en CPU

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-aplicacion
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3.2 HPA con CPU y Memoria

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-aplicacion
  minReplicas: 2
  maxReplicas: 15
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
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

### 3.3 HPA con Métricas Personalizadas

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mi-api
  minReplicas: 1
  maxReplicas: 50
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
```

---

## 4. EJEMPLO PRÁCTICO COMPLETO

### Paso 1: Crear Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
spec:
  selector:
    matchLabels:
      app: nginx-app
  template:
    metadata:
      labels:
        app: nginx-app
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
            memory: 256Mi
        ports:
        - containerPort: 80
```

### Paso 2: Crear HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

### Paso 3: Aplicar configuraciones

```bash
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml

# Verificar HPA
kubectl get hpa
kubectl describe hpa nginx-hpa

# Ver estado en tiempo real
kubectl get hpa nginx-hpa --watch
```

### Paso 4: Generar carga para pruebas

```bash
# Terminal 1: Monitorear HPA
kubectl get hpa --watch

# Terminal 2: Monitorear pods
kubectl get pods --watch

# Terminal 3: Generar carga
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://nginx-app; done"
```

---

## 5. MÉTRICAS Y MONITOREO

### Ver Métricas Actuales

```bash
# Métricas de nodos
kubectl top nodes

# Métricas de pods
kubectl top pods

# Métricas de un pod específico
kubectl top pod mi-pod -n default
```

### Consultar HPA

```bash
# Estado actual
kubectl get hpa
kubectl get hpa -o wide

# Detalles completos
kubectl describe hpa nginx-hpa

# Ver eventos
kubectl get events --sort-by='.lastTimestamp'
```

### Salida típica

```
NAME        REFERENCE                TARGETS            MINPODS   MAXPODS   REPLICAS   AGE
nginx-hpa   Deployment/nginx-app     45%/50%            2         10        3          5m
```

---

## 6. BUENAS PRÁCTICAS

### ✅ QUÉ HACER

1. **Definir requests y limits adecuados**
   ```yaml
   resources:
     requests:
       cpu: 100m
       memory: 128Mi
     limits:
       cpu: 500m
       memory: 512Mi
   ```

2. **Usar métricas múltiples**
   - CPU + Memoria para decisiones más informadas

3. **Establecer cooldown apropiado**
   - Evita oscilaciones ("flapping")

4. **Monitorear eventos de escalado**
   ```bash
   kubectl describe hpa nombre-hpa
   ```

5. **Probar con carga realista**
   - Usa herramientas como Apache Bench, wrk, o k6

### ❌ QUÉ EVITAR

1. **No establecer requests/limits**
   - HPA necesita datos de utilización porcentual

2. **Valores de target demasiado altos (>90%)**
   - Deja poco margen para picos

3. **Usar HPA sin monitoreo**
   - Implementa alertas en Prometheus/Grafana

4. **Mezclar HPA con Cluster Autoscaling sin cuidado**
   - Pueden entrar en conflicto

---

## 7. CASOS DE USO COMUNES

### API REST con tráfico variable
```yaml
minReplicas: 3
maxReplicas: 20
targetCPU: 70%
```

### Procesamiento de colas (Kafka, RabbitMQ)
```yaml
# Usar métrica personalizada: mensajes en cola
metrics:
- type: Pods
  pods:
    metric:
      name: queue_depth
    target:
      averageValue: "30"
```

### Microservicios con picos predecibles
```yaml
# Combinar HPA con escalado programado
# Implementar: CronJob para escalar antes de picos conocidos
```

---

## 8. TROUBLESHOOTING

### El HPA no escala

```bash
# Verificar Metrics Server
kubectl get deployment -n kube-system metrics-server

# Ver logs de Metrics Server
kubectl logs -n kube-system -l k8s-app=metrics-server

# Verificar requests/limits en el Deployment
kubectl describe deployment mi-app

# Ver eventos del HPA
kubectl describe hpa mi-hpa
```

### Error: "unable to compute replica count"

**Causa:** Sin métricas disponibles
**Solución:** 
- Esperar 1-2 minutos después de crear el Deployment
- Verificar que el pod esté corriendo y saludable
- Revisar logs del pod

### Oscilaciones continuas

**Causa:** Target muy bajo o fluctuaciones naturales
**Solución:**
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 600  # Aumentar
    policies:
    - type: Percent
      value: 25  # Reducir más lentamente
      periodSeconds: 60
```

---

## 9. HERRAMIENTAS ÚTILES

```bash
# Ver HPA con formato ampliado
kubectl get hpa -o json | jq '.items[] | {name: .metadata.name, minReplicas: .spec.minReplicas, maxReplicas: .spec.maxReplicas}'

# Monitorear cambios en tiempo real
kubectl get hpa --watch --all-namespaces

# Extraer estadísticas de escalado
kubectl get events -A --field-selector reason=SuccessfulRescale
```

---

## RESUMEN RÁPIDO

| Concepto | Descripción |
|----------|------------|
| **HPA v1** | Solo CPU, deprecated en 1.23+ |
| **HPA v2** | CPU, memoria, métricas personalizadas |
| **Metrics Server** | Requisito obligatorio |
| **Cycle time** | ~15-30 segundos |
| **Scale-up** | 3 minutos cooldown |
| **Scale-down** | 5 minutos cooldown |
| **Mínimo recomendado** | 2 replicas |
| **CPU target típico** | 70-80% |