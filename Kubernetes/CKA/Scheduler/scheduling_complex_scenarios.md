# Escenarios Complejos de Scheduling en Kubernetes

Este documento contiene ejemplos avanzados para el examen CKA, diseñados para practicar la combinación de múltiples restricciones de scheduling: Node Affinity, Pod Affinity, Anti-Affinity, y Tolerations de forma simultánea.

## 1. Alta Disponibilidad: Anti-Afinidad de Pods + Tolerancia + Node Affinity

**Objetivo:** Queremos desplegar 3 réplicas de una aplicación web. Para garantizar la disponibilidad máxima, se requiere:
1. Nunca deben ejecutarse dos réplicas en el mismo nodo (Pod Anti-Affinity).
2. Solo deben ejecutarse en nodos que estén en la zona `eu-west-1` (Node Affinity estricto).
3. Los nodos de esa zona tienen un taint de "dedicated=frontend:NoSchedule" que deben tolerar.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      # REGLA 3: Tolerancia al taint
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "frontend"
        effect: "NoSchedule"
      
      affinity:
        # REGLA 2: Node Affinity Estricto (Hard)
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - eu-west-1
                
        # REGLA 1: Pod Anti-Affinity (Repeler pods de la misma app)
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web
            topologyKey: "kubernetes.io/hostname" # Evalúa a nivel de Nodo individual
            
      containers:
      - name: nginx
        image: nginx
```

## 2. Dependencia de Caché y Evitación de Procesos Pesados

**Objetivo:** Tienes un Pod de Backend que *siempre* debe ejecutarse en el mismo nodo que un Pod de Redis (`app=cache`), pero además, no quieres que se despliegue en nodos donde exista un Pod de procesamiento pesado (`app=batch`).

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend-pod
  labels:
    app: backend
spec:
  affinity:
    # Atracción hacia el Pod de Caché
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - cache
        topologyKey: "kubernetes.io/hostname"
        
    # Repulsión a los Pods de Batch
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - batch
        topologyKey: "kubernetes.io/hostname"
        
  containers:
  - name: my-backend
    image: nginx
```

## 3. NodeSelectorTerms Múltiples (El concepto de OR y AND lógico)

**Objetivo:** El Pod debe programarse en nodos de la región `us-east` O en la región `us-west`. 
*Nota teórica vital:* Si se usan múltiples `nodeSelectorTerms`, funcionan como un operador lógico **OR** (con que se cumpla uno, basta). Si usamos múltiples `matchExpressions` dentro de un mismo term, es un **AND**.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-region-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        # TÉRMINO 1: Región us-east AND disco ssd (Ambos deben cumplirse)
        - matchExpressions:
          - key: region
            operator: In
            values:
            - us-east
          - key: diskType
            operator: In
            values:
            - ssd
            
        # O (OR) TÉRMINO 2: Región us-west (sin importar el disco)
        - matchExpressions:
          - key: region
            operator: In
            values:
            - us-west
            
  containers:
  - name: ubuntu
    image: ubuntu
    command: ["sleep", "3600"]
```
