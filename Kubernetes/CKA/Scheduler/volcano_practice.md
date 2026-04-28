# Volcano Scheduler

Volcano es un sistema de batch scheduling nativo para Kubernetes, diseñado específicamente para cargas de trabajo de alto rendimiento como Machine Learning, Deep Learning, Bioinformática y análisis de Big Data.

## ¿Por qué usar Volcano en lugar del Kube-Scheduler?

El `kube-scheduler` por defecto evalúa e inicia los Pods uno por uno. Volcano introduce el concepto de **Gang Scheduling** (Programación en grupo). 

Imagina que tienes un trabajo distribuido de Machine Learning que requiere estrictamente de 4 Pods simultáneos para coordinarse entre sí. Si tu clúster solo tiene espacio libre para 3, el scheduler nativo lanzará esos 3 y dejará el cuarto en "Pending". Esto desperdicia recursos porque los 3 no pueden hacer nada útil sin el cuarto Pod. 
**Volcano** esperará hasta que haya recursos garantizados para los 4 y los lanzará *todos a la vez*.

---

## 1. Instalación de Volcano

La forma más rápida de instalarlo en tu clúster local de pruebas es aplicar el manifiesto de desarrollo directamente desde su repositorio oficial en GitHub.

```bash
kubectl apply -f https://raw.githubusercontent.com/volcano-sh/volcano/master/installer/volcano-development.yaml
```

Verifica que los componentes se están ejecutando (puede tardar un minuto en descargar las imágenes):
```bash
kubectl get pods -n volcano-system
```
Deberías ver Pods para el `volcano-scheduler`, `volcano-admission`, y `volcano-controllers`.

---

## 2. Prueba Práctica: Gang Scheduling

Volcano introduce un Custom Resource Definition (CRD) llamado `Job` en el grupo `batch.volcano.sh` (comúnmente nos referimos a él como `vcjob`).

Vamos a simular un trabajo que requiere de 2 Pods para ejecutarse.

**1. Crea un archivo `volcano-job.yaml`:**

```yaml
apiVersion: batch.volcano.sh/v1alpha1
kind: Job
metadata:
  name: test-volcano-job
spec:
  minAvailable: 2 # Gang scheduling: Necesita poder iniciar al menos 2 Pods simultáneamente para empezar
  schedulerName: volcano # Especifica explícitamente que use el scheduler de Volcano
  tasks:
    - replicas: 2 # Número de Pods que intentaremos levantar para esta tarea
      name: test-task
      template:
        spec:
          containers:
            - name: busybox
              image: busybox
              command: ["sh", "-c", "echo 'Trabajando en grupo...' && sleep 300"]
              resources:
                requests:
                  cpu: "200m"
          restartPolicy: OnFailure
```

**2. Aplica el trabajo en tu clúster:**
```bash
kubectl apply -f volcano-job.yaml
```

**3. Verifica el estado:**
```bash
# Ver el estado global del trabajo de Volcano
kubectl get vcjob test-volcano-job

# Ver los pods individuales generados por Volcano
kubectl get pods -l volcano.sh/job-name=test-volcano-job
```

### ¿Qué está pasando aquí?
- **`minAvailable: 2`**: Esta es la clave del Gang Scheduling. Le indica a Volcano que reserve recursos pero que no inicie *ningún* contenedor hasta que esté 100% seguro de que puede iniciar los 2 que pide la tarea.
- **`schedulerName: volcano`**: Instruye a Kubernetes para que ignore el `kube-scheduler` por defecto para estos pods y le pase el control a Volcano.

---

## 3. Otros Recursos Clave de Volcano (CRDs)

Aparte del `Job` (o `vcjob`), Volcano instala otros Custom Resources (CRDs) muy importantes que le dan su potencia en entornos empresariales:

### A. Queue (Colas)
Las colas son fundamentales en Volcano. Cuando envías un `vcjob`, siempre se asigna a una cola (si no especificas ninguna, va a la cola `default`). 
- **¿Para qué sirve?** Sirve para dividir los recursos del clúster entre diferentes equipos o proyectos. Por ejemplo, puedes crear una cola `data-science` con un "peso" de 3, y una cola `backend` con un peso de 1.
- **Fair-share (Reparto justo):** Si ambos equipos envían muchos trabajos simultáneos, Volcano utilizará el algoritmo de proporción para garantizar que el equipo de `data-science` obtenga el 75% de los recursos y `backend` el 25%, evitando que un equipo monopolice el clúster.

**Ejemplo de creación de una Queue:**
```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: data-science-queue
spec:
  weight: 3 # Peso relativo para la repartición de recursos
  capability:
    cpu: "10" # Límite máximo (hard limit) que esta cola puede consumir
```

### B. PodGroup
El `PodGroup` es el verdadero motor detrás del "Gang Scheduling". 
- Cuando creas un `vcjob`, Volcano crea automáticamente un `PodGroup` por debajo para agrupar las tareas.
- **¿Por qué es importante saberlo?** Porque Volcano no te obliga a usar siempre su `vcjob`. Si prefieres usar recursos nativos de Kubernetes (como un `Deployment` normal, un `StatefulSet` o un `Job` estándar), puedes crear manualmente un `PodGroup` e instruir a tus Pods nativos para que pertenezcan a ese grupo usando la anotación `scheduling.k8s.io/group-name`. ¡Así consigues Gang Scheduling en recursos estándar!

### C. Arquitectura de Plugins (Scheduler Plugins)
A diferencia del scheduler tradicional, el cerebro de Volcano está dividido en **Plugins** independientes que se ejecutan en cadena. Puedes activarlos, desactivarlos o cambiar su configuración editando el ConfigMap del scheduler. Los más importantes son:
- **gang:** Se encarga de verificar que la regla de `minAvailable` se cumpla estrictamente antes de asignar los Pods a los nodos.
- **drf (Dominant Resource Fairness):** Un algoritmo matemático avanzado que asegura un reparto justo cuando los trabajos piden distintos tipos de recursos (ej. un trabajo pide mucha CPU y poca RAM, mientras otro pide mucha RAM y poca CPU).
- **proportion:** Reparte los recursos equitativamente basándose en el "peso" (weight) de las `Queues`.
- **binpack:** Intenta concentrar la carga llenando los nodos al máximo antes de usar nodos nuevos. Esto es ideal para auto-escalado en la nube, ya que permite apagar nodos vacíos y ahorrar costes.

---

**💡 Tip para tu estudio:** 
Aunque Volcano es fascinante, recuerda que **no te lo evaluarán en el examen CKA**. El examen oficial se centra únicamente en el scheduler nativo, nodeSelectors, Taints/Tolerations, y a lo sumo cómo cambiar el nombre del scheduler (lo que vimos en el archivo anterior). Sin embargo, entender los `PodGroups` y cómo funcionan los plugins de Volcano te dará un contexto invaluable para tu vida profesional administrando clústeres.
