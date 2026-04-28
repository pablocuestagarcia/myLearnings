# Prácticas de Scheduling en Kubernetes (CKA)

Esta guía contiene ejercicios prácticos y teoría para que domines los conceptos de scheduling, fundamentales para el examen CKA.

---

## 1. Manual Scheduling (Asignación Manual)

Normalmente, el `kube-scheduler` decide en qué nodo se ejecuta un Pod. Sin embargo, puedes saltarte el scheduler asignando el Pod manualmente a un nodo usando el campo `nodeName`. 

Esto es muy útil en el examen si te piden desplegar un Pod en un clúster que no tiene el `kube-scheduler` funcionando.

**Práctica:**
Crea un archivo `manual-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: manual-scheduled-pod
spec:
  nodeName: cka-cluster-worker # <-- El Pod irá directamente a este nodo
  containers:
  - name: nginx
    image: nginx
```
Aplica y verifica:
```bash
kubectl apply -f manual-pod.yaml
kubectl get pod manual-scheduled-pod -o wide
```

---

## 2. Labels y Selectors (nodeSelector)

Para dirigir Pods a nodos con características específicas (por ejemplo, nodos con discos SSD o GPUs), usamos etiquetas (labels) en los nodos y `nodeSelector` en los Pods.

**Práctica:**

1. **Añade una etiqueta al nodo:**
   ```bash
   kubectl label nodes cka-cluster-worker2 disk=ssd
   ```

2. **Verifica la etiqueta:**
   ```bash
   kubectl get nodes --show-labels | grep disk=ssd
   ```

3. **Despliega un Pod que requiera esa etiqueta (`selector-pod.yaml`):**
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: node-selector-pod
   spec:
     containers:
     - name: nginx
       image: nginx
     nodeSelector:
       disk: ssd # <-- El Pod solo se programará en nodos con esta etiqueta
   ```
   ```bash
   kubectl apply -f selector-pod.yaml
   ```

---

## 3. Taints y Tolerations

Los **Taints** se aplican a los nodos para "repeler" Pods. Los **Tolerations** se aplican a los Pods para permitirles ser programados en nodos con Taints específicos.
*Ojo: Un Toleration NO garantiza que el Pod vaya a ese nodo, solo le da "permiso" para ir.*

**Práctica:**

1. **Añade un Taint a un nodo:**
   ```bash
   kubectl taint nodes cka-cluster-worker color=blue:NoSchedule
   ```
   *(Cualquier Pod nuevo que no tolere `color=blue` no será programado en `cka-cluster-worker`)*

2. **Crea un Pod con la Toleration adecuada (`toleration-pod.yaml`):**
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: toleration-pod
   spec:
     containers:
     - name: nginx
       image: nginx
     tolerations:
     - key: "color"
       operator: "Equal"
       value: "blue"
       effect: "NoSchedule"
   ```
   ```bash
   kubectl apply -f toleration-pod.yaml
   ```

**Para eliminar el taint después de la práctica**, usa el mismo comando pero con un signo menos al final: 
`kubectl taint nodes cka-cluster-worker color=blue:NoSchedule-`

---

## 4. Custom Schedulers (Otros Schedulers)

¿Existen otros schedulers en Kubernetes? **Sí**. Kubernetes permite ejecutar múltiples schedulers simultáneamente en el mismo clúster. 

Esto es útil si tienes cargas de trabajo muy específicas (por ejemplo, Machine Learning, HPC, o procesos batch) que requieren algoritmos de decisión distintos al `kube-scheduler` por defecto.

### ¿Cómo se despliegan?

Un scheduler personalizado es simplemente otra aplicación (normalmente empaquetada en un Pod o Deployment). A menudo, es otra instancia del mismo binario de `kube-scheduler` pero configurado con un nombre diferente y reglas distintas.

Para desplegarlo:
1. Creas un `ServiceAccount`, `ClusterRole`, y `ClusterRoleBinding` para darle permisos al nuevo scheduler de leer nodos/pods y actualizar el estado de los Pods.
2. Despliegas el scheduler (usualmente en el namespace `kube-system`) pasándole el argumento `--scheduler-name=my-custom-scheduler`.
3. (Opcional) Configuras un archivo de configuración de KubeSchedulerConfiguration para definir perfiles específicos si estás extendiendo el scheduler nativo.

### ¿Cómo se utilizan?

Una vez desplegado tu scheduler secundario, los Pods seguirán usando el scheduler por defecto a menos que se lo indiques explícitamente en el `spec`.

Para usarlo, simplemente añades el campo `schedulerName` al manifiesto del Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-scheduled-pod
spec:
  schedulerName: my-custom-scheduler # <-- Nombre de tu scheduler personalizado
  containers:
  - name: nginx
    image: nginx
```

Si el `my-custom-scheduler` no está funcionando o configurado incorrectamente, el Pod se quedará en estado `Pending` indefinidamente, ya que el scheduler por defecto lo ignorará.
