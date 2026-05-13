# Práctica de Scheduling para CKA

Este documento contiene ejercicios prácticos resueltos para cada uno de los conceptos de scheduling evaluados en el examen CKA. Te ayudará a prepararte para los escenarios prácticos del examen.

## 1. Manual Scheduling

**Objetivo:** Crear un Pod y asignarlo manualmente a un nodo específico sin usar el scheduler de Kubernetes.

**Ejercicio:**
1. Identifica un nodo en tu clúster (ej. `node01`).
2. Crea un Pod llamado `manual-pod` usando la imagen `nginx:alpine`.
3. Asígnalo forzosamente al nodo elegido sin utilizar el campo `nodeSelector`.

**Solución:**
```yaml
# manual-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: manual-pod
spec:
  nodeName: node01 # Asignación explícita saltando el scheduler
  containers:
  - name: nginx
    image: nginx:alpine
```
```bash
# Aplicar el manifiesto y verificar en qué nodo se está ejecutando
kubectl apply -f manual-pod.yaml
kubectl get pod manual-pod -o wide 
```

## 2. Node Selector y Labels

**Objetivo:** Etiquetar un nodo y usar `nodeSelector` para que un Pod solo se programe en nodos con esa etiqueta específica.

**Ejercicio:**
1. Añade la etiqueta `hardware=gpu` a un nodo worker de tu clúster.
2. Crea un Pod llamado `gpu-pod` con la imagen `redis` que solo se programe en nodos que contengan esa etiqueta.

**Solución:**
```bash
# 1. Etiquetar el nodo (reemplaza <node-name> por tu nodo)
kubectl label nodes <node-name> hardware=gpu

# Opcional: Verificar que el nodo tiene la etiqueta
kubectl get nodes -l hardware=gpu
```

```yaml
# gpu-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  nodeSelector:
    hardware: gpu
  containers:
  - name: redis
    image: redis
```
```bash
# 2. Crear el pod
kubectl apply -f gpu-pod.yaml
```

## 3. Taints y Tolerations

**Objetivo:** Aislar un nodo mediante un taint (mancha) y permitir que solo Pods con la tolerancia adecuada puedan programarse en él.

**Ejercicio:**
1. Aplica un taint a un nodo worker con la clave `env`, el valor `prod` y el efecto `NoSchedule`.
2. Crea un Pod llamado `prod-pod` con la imagen `nginx` que tolere este taint explícitamente para poder ser programado en él.

**Solución:**
```bash
# 1. Aplicar el Taint al nodo
kubectl taint nodes <node-name> env=prod:NoSchedule
```

```yaml
# prod-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: prod-pod
spec:
  containers:
  - name: nginx
    image: nginx
  tolerations:
  - key: "env"
    operator: "Equal"
    value: "prod"
    effect: "NoSchedule"
```
```bash
# 2. Crear el pod
kubectl apply -f prod-pod.yaml
```

## 4. Node Affinity

**Objetivo:** Usar `NodeAffinity` para programar un Pod indicando una preferencia (no un requisito estricto) hacia ciertos nodos.

**Ejercicio:**
1. Crea un Pod llamado `affinity-pod` con la imagen `httpd`.
2. Configura una afinidad de nodo preferida (`preferredDuringSchedulingIgnoredDuringExecution`) para que el scheduler intente colocar el Pod en nodos con la etiqueta `disktype=ssd`.

**Solución:**
```yaml
# affinity-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: affinity-pod
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
  containers:
  - name: httpd
    image: httpd
```
```bash
kubectl apply -f affinity-pod.yaml
```

## 5. Pod Anti-affinity

**Objetivo:** Asegurar que dos o más réplicas de una aplicación no se programen en el mismo nodo para garantizar la alta disponibilidad (tolerancia a fallos de nodo).

**Ejercicio:**
1. Crea un Deployment llamado `web-app` con 3 réplicas de la imagen `nginx` y la etiqueta `app=web`.
2. Configura `podAntiAffinity` estricta (`requiredDuringSchedulingIgnoredDuringExecution`) para que ninguna réplica de este Deployment comparta el mismo nodo (basado en el `topologyKey: "kubernetes.io/hostname"`).

**Solución:**
```yaml
# web-app-anti-affinity.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
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
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - web
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: nginx
        image: nginx
```
```bash
kubectl apply -f web-app-anti-affinity.yaml
# Nota: Si tu clúster tiene menos de 3 nodos worker, algunas réplicas se quedarán en estado 'Pending'.
```

## 6. Resource Requests y Limits

**Objetivo:** Definir cuántos recursos necesita un contenedor para iniciarse y cuál es su límite máximo de consumo.

**Ejercicio:**
1. Crea un Pod llamado `resource-pod` con la imagen `busybox` ejecutando el comando `sleep 3600`.
2. Configura el contenedor para que solicite (`requests`) 100m de CPU y 128Mi de Memoria.
3. Establece los límites (`limits`) del contenedor en 200m de CPU y 256Mi de Memoria.

**Solución:**
```yaml
# resource-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-pod
spec:
  containers:
  - name: busybox
    image: busybox
    command: ["sleep", "3600"]
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
```
```bash
kubectl apply -f resource-pod.yaml
```

## 7. Múltiples Schedulers

**Objetivo:** Desplegar un Pod indicando que debe ser procesado por un scheduler secundario/personalizado.

**Ejercicio:**
1. Asume que en tu clúster existe un scheduler personalizado corriendo bajo el nombre `my-custom-scheduler`.
2. Crea un Pod llamado `custom-sch-pod` con la imagen `nginx` que utilice explícitamente este nuevo scheduler.

**Solución:**
```yaml
# custom-sch-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-sch-pod
spec:
  schedulerName: my-custom-scheduler # Indicamos el scheduler a usar
  containers:
  - name: nginx
    image: nginx
```
```bash
kubectl apply -f custom-sch-pod.yaml
# Si el scheduler 'my-custom-scheduler' no está corriendo realmente, el pod se quedará 'Pending'.
```
