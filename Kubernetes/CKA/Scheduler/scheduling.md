# Scheduling en Kubernetes

El scheduling es el proceso mediante el cual Kubernetes decide en qué nodo (node) debe ejecutarse un Pod. El componente responsable de esto es el `kube-scheduler`. Evalúa los requisitos del Pod y el estado de los nodos para encontrar el lugar más adecuado. En el contexto de la certificación CKA, comprender cómo influir y controlar este comportamiento es fundamental.

## Manual Scheduling

Si un Pod no tiene un `nodeName` especificado y no hay un scheduler ejecutándose (o queremos saltárnoslo), el Pod se quedará en estado `Pending`.
El **Manual Scheduling** consiste en asignar explícitamente un Pod a un nodo asignando el nombre del nodo al campo `nodeName` dentro de la especificación del Pod (`spec.nodeName`).
Una vez que el Pod ha sido creado, este campo no puede ser modificado. Si necesitas mover el Pod, debes eliminarlo y crear uno nuevo. Si no puedes crear el Pod de nuevo y ya existe en estado Pending, puedes crear un objeto `Binding` y enviar una petición POST a la API de Kubernetes para simular lo que hace el scheduler.

## Node Selector

`nodeSelector` es la forma más sencilla de recomendar o forzar a un Pod a programarse en un conjunto específico de nodos. Funciona mediante la coincidencia de etiquetas (labels) clave-valor.
Debes agregar el campo `nodeSelector` a la especificación del Pod y especificar los labels que el nodo de destino debe tener. Si ningún nodo coincide con las etiquetas, el Pod se quedará en estado `Pending`.

### Labels

Los Labels son pares clave-valor que se adjuntan a los objetos de Kubernetes, como los Nodos. Sirven para identificar atributos de los objetos que son relevantes y significativos para los usuarios. Para que `nodeSelector` funcione, los nodos deben haber sido etiquetados previamente (ej. `kubectl label nodes <node-name> <key>=<value>`).

## Taints and Tolerations

A diferencia de la afinidad (que atrae Pods a Nodos), los **Taints** (manchas) repelen Pods de los Nodos. Si un nodo tiene un taint, ningún pod puede programarse en él a menos que el pod tenga una **Toleration** (tolerancia) correspondiente.
*   **Taints**: Se aplican a los nodos (`kubectl taint nodes <node-name> key=value:effect`). Los efectos pueden ser `NoSchedule` (no programa pods nuevos), `PreferNoSchedule` (intenta no programarlos), o `NoExecute` (expulsa los pods existentes si no lo toleran).
*   **Tolerations**: Se aplican a los Pods en su especificación. Un Pod con una tolerancia "tolera" el taint del nodo, permitiendo (pero no forzando) su programación en él.

## Affinity and Anti-affinity

Proporcionan un control mucho más granular que `nodeSelector`.
*   **Node Affinity**: Similar a `nodeSelector`, permite restringir en qué nodos se puede programar el Pod según los labels del nodo. Soporta operadores más ricos (In, NotIn, Exists, DoesNotExist, Gt, Lt) y reglas "suaves" (`preferredDuringSchedulingIgnoredDuringExecution`) frente a reglas "duras" (`requiredDuringSchedulingIgnoredDuringExecution`).
*   **Pod Affinity / Anti-affinity**: Permite programar pods en base a los labels de **otros pods** que ya se están ejecutando en el nodo (o en otros dominios topológicos), en lugar de los labels del nodo en sí. Esto sirve para asegurar que ciertos pods corran juntos (ej. web y caché) o separados (ej. réplicas de la misma base de datos para alta disponibilidad).

## Resource Requests and Limits

El scheduler también tiene en cuenta los recursos.
*   **Requests**: La cantidad mínima de CPU/Memoria garantizada para un contenedor. El scheduler usa este valor para decidir en qué nodo colocar el Pod. Si un nodo no tiene suficiente capacidad no asignada para satisfacer las *requests* del Pod, no lo programará ahí.
*   **Limits**: El máximo absoluto que un contenedor puede usar. No afecta al scheduler en la colocación inicial tanto como las *requests*, pero sí al comportamiento del nodo en tiempo de ejecución (Throttling para CPU, OOMKill para Memoria).

## Pod Topology Spread Constraints

Permiten controlar cómo los Pods se distribuyen a lo largo del clúster entre diferentes dominios topológicos (como regiones, zonas, nodos o cualquier otro dominio definido por el usuario).
Esto ayuda a lograr alta disponibilidad y una utilización eficiente de los recursos, evitando que todos los Pods de un despliegue acaben en el mismo nodo o zona, configurando la máxima asimetría permitida (`maxSkew`).

## Priority Classes y Preemption

Las **Priority Classes** (Clases de Prioridad) son objetos de Kubernetes que permiten asignar un "peso" o nivel de importancia a los Pods. Se relacionan directamente con el scheduling para resolver problemas de contención de recursos.

Su relación con el scheduling se basa en dos mecanismos clave:
1. **Orden en la cola de programación (Scheduling Queue)**: Cuando hay múltiples Pods pendientes, el scheduler da preferencia a los que tienen una mayor prioridad, evaluándolos y asignándolos a los nodos antes que a los de menor prioridad.
2. **Preemption (Desalojo o Apropiación)**: Si un Pod de alta prioridad no encuentra ningún nodo con recursos suficientes, el scheduler buscará nodos donde pueda expulsar (evict) a Pods de menor prioridad. Al desalojar estos Pods, libera los recursos necesarios para poder programar el Pod de alta prioridad.

## Múltiples Schedulers

En un mismo clúster de Kubernetes puede haber más de un scheduler ejecutándose simultáneamente. Por defecto, se usa el `default-scheduler`.
Si se despliega un scheduler personalizado, se puede instruir a un Pod para que sea programado por ese scheduler específico agregando el campo `schedulerName: <nombre-de-tu-scheduler>` en la especificación del Pod.

---

## Ejemplos Prácticos

### 1. Ejemplo Sencillo: Manual Scheduling y NodeSelector

Este ejemplo muestra cómo asignar un pod a un nodo concreto mediante `nodeName` y otro mediante `nodeSelector`.

Primero, etiquetamos el nodo:
```bash
kubectl label nodes worker-node-1 disk=ssd
```

Archivo de manifiesto `simple-scheduling.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-manual
spec:
  nodeName: worker-node-1 # El pod irá forzosamente a este nodo, saltando el scheduler.
  containers:
  - name: nginx
    image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-nodeselector
spec:
  nodeSelector:
    disk: ssd # El pod solo irá a nodos con este label.
  containers:
  - name: redis
    image: redis
```

### 2. Ejemplo Avanzado: Taints, Tolerations, Node Affinity y Resource Requests

En este escenario queremos desplegar una aplicación crítica. Se tienen nodos dedicados para bases de datos marcados con taints. Queremos asegurar que:
1. El Pod tolere el Taint del nodo de la base de datos.
2. Exija preferiblemente (Soft Node Affinity) nodos de la zona "eu-west-1".
3. Solicite recursos específicos para que el scheduler lo coloque solo en un nodo con la capacidad adecuada.

Primero, simulamos el taint en el nodo:
```bash
kubectl taint nodes db-node-1 type=database:NoSchedule
kubectl label nodes db-node-1 zone=eu-west-1
```

Archivo de manifiesto `advanced-scheduling.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: critical-db-pod
spec:
  tolerations:
  - key: "type"
    operator: "Equal"
    value: "database"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - eu-west-1
  containers:
  - name: postgres
    image: postgres:13
    env:
    - name: POSTGRES_PASSWORD
      value: "secret"
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
```

### 3. Ejemplo Práctico: Priority Class y Preemption

En este ejemplo, definimos una PriorityClass y luego la asignamos a un Pod. Si el clúster estuviera lleno de Pods sin prioridad, este Pod crítico expulsaría a algunos de ellos para liberar recursos y poder ejecutarse.

Archivo de manifiesto `priority-class.yaml`:
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-class
value: 1000000
globalDefault: false # Si fuera true, los pods sin priorityClassName adoptarían este valor por defecto.
description: "Esta clase de prioridad es para los Pods críticos del entorno."
```

Archivo de manifiesto `pod-with-priority.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: critical-nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx
  priorityClassName: high-priority-class # Vinculamos el Pod a la Priority Class
```

---

## Consejos y Técnicas para el Examen CKA (YAML e Indentación)

El formato YAML se basa estrictamente en la alineación visual mediante espacios en blanco. Un error de un solo espacio invalidará tu manifiesto. Dado que en el examen estarás bajo presión, aquí tienes las técnicas más efectivas para asegurar que tu código sea válido:

### 1. La Técnica de "La Escalera de los 2 Espacios" (Acrónimo SAN-R-NM)

Olvídate de intentar recordar cuántos espacios totales hay desde el margen izquierdo. Piensa en **"escalones" de exactamente 2 espacios**. Cada vez que declaras una propiedad anidada, bajas un escalón (+2 espacios a la derecha).

Aprende el acrónimo **SAN-R-NM** (Piensa en un **San**atorio de **R**esona**N**cia **M**agnética) para el bloque más difícil del examen, el `affinity`:

*   **S** `spec:` (Escalón 0)
*   **A** `  affinity:` (Escalón 1: +2)
*   **N** `    nodeAffinity:` (Escalón 2: +2)
*   **R** `      requiredDuringScheduling...:` (Escalón 3: +2)
*   **N** `        nodeSelectorTerms:` (Escalón 4: +2)
*   **M** `        - matchExpressions:` (Escalón 5: La lista)

### 2. La Regla del "Guion de la Lista" (El Guion es el Límite)

El mayor error ocurre al alinear listas (arrays). Usa esta regla visual inquebrantable: **El guion (`-`) ocupa el lugar del primer espacio del siguiente escalón y va alineado verticalmente con la primera letra de su propiedad padre.**

```yaml
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:    # <-- El guion va exactamente debajo de la 'n' de nodeSelectorTerms
          - key: mi-label      # <-- El guion va exactamente debajo de la 'm' de matchExpressions
            operator: In
            values:
            - valor1           # <-- El guion debajo de la 'v' de values
```

### 3. El Salvavidas: `kubectl explain --recursive`

Si en el examen tu mente se queda en blanco o el YAML no compila y no encuentras el error, **no intentes adivinar ni pelear con los espacios**. Usa el manual integrado de Kubernetes:

```bash
kubectl explain pod.spec.affinity.nodeAffinity --recursive
```

Este comando imprimirá en tu pantalla la estructura jerárquica exacta con su nivel de anidación nativo. Solo debes fijarte visualmente en qué bloque va dentro de qué bloque y replicarlo en tu fichero.

### 4. Generación Básica Imperativa (No empieces de cero)

Nunca escribas la estructura base de un Pod o Deployment a mano. Utiliza la CLI para que te genere el esqueleto inicial perfectamente indentado y edítalo añadiendo la afinidad después:

```bash
kubectl run test-pod --image=nginx --dry-run=client -o yaml > pod.yaml
```

### 5. Configuración de Vim (Tu primer paso en el examen)

Al inicio de tu examen CKA, lo primero que deberías hacer en la terminal es configurar tu editor Vim para evitar que se mezclen tabuladores y espacios, ahorrándote horas de frustración:

```bash
echo "set tabstop=2 shiftwidth=2 expandtab" >> ~/.vimrc
```

*   `tabstop=2`: Las tabulaciones miden 2 espacios visuales.
*   `shiftwidth=2`: Al pulsar las teclas de indentación automática (`>>` o `<<`), se mueve 2 espacios.
*   `expandtab`: Esto es **VITAL**. Convierte la tecla física de "Tab" de tu teclado en espacios. En YAML, usar una tabulación real (un caracter "\t") está prohibido y romperá tu código. Con esto, puedes usar el Tabulador y Vim insertará dos espacios mágicamente.