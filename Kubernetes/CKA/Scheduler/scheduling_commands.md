# Comandos Útiles de Scheduling en Kubernetes

A continuación se presenta una tabla con los comandos de `kubectl` más relevantes para gestionar, depurar y configurar el scheduling en Kubernetes, muy útiles de cara al examen CKA y para administración general.

| Comando | Descripción | Concepto Relacionado |
| :--- | :--- | :--- |
| `kubectl get pods -o wide` | Muestra la lista de Pods indicando en qué nodo se está ejecutando cada uno. | Scheduling General |
| `kubectl describe pod <pod-name>` | Muestra información detallada del Pod. Revisa la sección `Events` al final para ver las decisiones del `kube-scheduler` y saber por qué un Pod está `Pending`. | Troubleshooting |
| `kubectl get nodes --show-labels` | Lista todos los nodos y muestra sus etiquetas (labels) actuales. | Node Selector / Affinity |
| `kubectl label nodes <node-name> <key>=<value>` | Añade o modifica una etiqueta en un nodo específico. | Node Selector / Affinity |
| `kubectl label nodes <node-name> <key>-` | Elimina una etiqueta de un nodo específico. (Nota el `-` al final). | Node Selector / Affinity |
| `kubectl taint nodes <node-name> <key>=<value>:<effect>` | Aplica un Taint a un nodo. El `<effect>` puede ser `NoSchedule`, `PreferNoSchedule` o `NoExecute`. | Taints and Tolerations |
| `kubectl taint nodes <node-name> <key>=<value>:<effect>-` | Elimina un Taint específico de un nodo. (Nota el `-` al final). | Taints and Tolerations |
| `kubectl taint nodes <node-name> <key>-` | Elimina todos los Taints asociados a esa clave en un nodo. | Taints and Tolerations |
| `kubectl describe node <node-name> \| grep -i taint` | Busca y visualiza los Taints configurados actualmente en un nodo. | Taints and Tolerations |
| `kubectl cordon <node-name>` | Marca un nodo como no programable (`SchedulingDisabled`). Evita que nuevos Pods se desplieguen allí, pero no expulsa a los existentes. | Mantenimiento / Manual |
| `kubectl uncordon <node-name>` | Vuelve a marcar un nodo como programable, permitiendo que el scheduler le asigne nuevos Pods. | Mantenimiento / Manual |
| `kubectl drain <node-name> --ignore-daemonsets` | Expulsa (evict) de forma segura los Pods de un nodo (requiere `--ignore-daemonsets` si hay DaemonSets) y lo marca como `cordon`. | Mantenimiento / Eviction |
| `kubectl get priorityclass` | Lista las Priority Classes definidas en el clúster. | Priority Classes |
| `kubectl top nodes` / `kubectl top pods` | Muestra el consumo actual de CPU y Memoria (requiere tener instalado el `metrics-server`). Útil para ver disponibilidad. | Resource Requests & Limits |
