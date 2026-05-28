# Guía de Mantenimiento de Cluster Kubernetes (CKA)

> **Cobertura:** Actualización de nodos · Upgrade de versión · Backups & Restore · etcd · Velero

---

## Tabla de Contenidos

1. [Conceptos Previos](#conceptos-previos)
2. [Actualización de Versión de Kubernetes](#actualización-de-versión-de-kubernetes)
   - [Control Plane](#control-plane)
   - [Worker Nodes](#worker-nodes)
3. [Gestión de Nodos: Drain, Cordon y Uncordon](#gestión-de-nodos)
4. [etcd: Backups y Restore](#etcd-backups-y-restore)
   - [¿Qué es etcd?](#qué-es-etcd)
   - [Backup de etcd](#backup-de-etcd)
   - [Restore de etcd](#restore-de-etcd)
5. [Velero: Backup a Nivel de Cluster](#velero-backup-a-nivel-de-cluster)
   - [¿Por qué Velero?](#por-qué-velero)
   - [Instalación](#instalación)
   - [Crear un Backup](#crear-un-backup)
   - [Restore con Velero](#restore-con-velero)
   - [Schedules y Políticas](#schedules-y-políticas)
6. [Otras Herramientas de Backup](#otras-herramientas-de-backup)
7. [Cheatsheet para el Examen CKA](#cheatsheet-para-el-examen-cka)

---

## Conceptos Previos

Antes de entrar en materia, conviene tener claros estos puntos:

- **kubeadm**: Herramienta oficial para bootstrapping y upgrades de clusters. Es la que usa el CKA.
- **kubelet**: Agente que corre en cada nodo. Se actualiza de forma independiente.
- **kubectl**: CLI de cliente. No afecta al cluster si está en una versión ligeramente distinta.
- **Regla de versiones**: Kubernetes garantiza compatibilidad entre componentes que difieran en ±1 versión menor (`minor`). Nunca saltes más de una versión menor en un upgrade.
- **etcd**: Base de datos clave-valor que almacena **todo** el estado del cluster. Es el componente más crítico a la hora de hacer backups.

---

## Actualización de Versión de Kubernetes

### Flujo General

```
1. Upgrade del control plane (nodo por nodo si hay varios)
2. Upgrade de los worker nodes (uno a uno, drenando cada uno)
3. Verificación final
```

> ⚠️ **Nunca** actualices más de una versión menor a la vez. Si estás en `1.28.x`, el siguiente paso es `1.29.x`, nunca `1.30.x`.

---

### Control Plane

#### 1. Comprobar versión actual

```bash
kubectl get nodes
kubeadm version
kubelet --version
kubectl version --short
```

#### 2. Identificar la siguiente versión disponible

```bash
# En sistemas Debian/Ubuntu
apt-cache madison kubeadm | head -10

# En sistemas RHEL/CentOS
yum list --showduplicates kubeadm
```

#### 3. Actualizar kubeadm en el nodo Control Plane

```bash
# Desmarcar el paquete como held
apt-mark unhold kubeadm

# Instalar la versión objetivo (ejemplo: 1.29.0-1.1)
apt-get update
apt-get install -y kubeadm=1.29.0-1.1

# Volver a marcar como held para evitar actualizaciones accidentales
apt-mark hold kubeadm

# Verificar
kubeadm version
```

#### 4. Plan de upgrade

```bash
# Muestra qué se va a actualizar y detecta incompatibilidades
kubeadm upgrade plan
```

La salida incluye:
- Versión actual de cada componente
- Versión objetivo disponible
- Advertencias si hay algo fuera de lugar

#### 5. Aplicar el upgrade

```bash
# Sustituye X.Y.Z por la versión objetivo
kubeadm upgrade apply v1.29.0

# Para nodos control plane adicionales (multi-master):
kubeadm upgrade node
```

> El comando `upgrade apply` actualiza: `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `kube-proxy` y `CoreDNS`. **No** actualiza `kubelet` ni `kubectl`.

#### 6. Drain del nodo control plane (si se actualiza kubelet)

```bash
# Marcar el nodo como no programable y evacuar los pods
kubectl drain <control-plane-node> --ignore-daemonsets --delete-emptydir-data
```

#### 7. Actualizar kubelet y kubectl

```bash
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.29.0-1.1 kubectl=1.29.0-1.1
apt-mark hold kubelet kubectl

# Recargar systemd y reiniciar kubelet
systemctl daemon-reload
systemctl restart kubelet
```

#### 8. Volver a poner el nodo en servicio

```bash
kubectl uncordon <control-plane-node>
```

#### 9. Verificar estado

```bash
kubectl get nodes
# El control plane debería mostrar la nueva versión
```

---

### Worker Nodes

El proceso se repite para cada worker, **uno a la vez**, para mantener la disponibilidad.

#### 1. Actualizar kubeadm en el worker

```bash
# Ejecutar en el nodo worker (SSH)
apt-mark unhold kubeadm
apt-get install -y kubeadm=1.29.0-1.1
apt-mark hold kubeadm
```

#### 2. Actualizar la configuración del nodo

```bash
# Ejecutar en el nodo worker
kubeadm upgrade node
```

#### 3. Drenar el nodo (desde el control plane o con acceso al cluster)

```bash
# Ejecutar desde donde tengas acceso a kubectl
kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data
```

> `--ignore-daemonsets`: Los DaemonSets no se mueven, se ignoran.  
> `--delete-emptydir-data`: Acepta perder datos en volúmenes emptyDir.

#### 4. Actualizar kubelet y kubectl en el worker

```bash
# Ejecutar en el nodo worker
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.29.0-1.1 kubectl=1.29.0-1.1
apt-mark hold kubelet kubectl

systemctl daemon-reload
systemctl restart kubelet
```

#### 5. Volver a poner el nodo en servicio

```bash
# Ejecutar desde control plane
kubectl uncordon <worker-node>

# Verificar
kubectl get nodes
```

#### 6. Repetir para cada worker

---

## Gestión de Nodos

Estas operaciones son parte del mantenimiento diario y esenciales para upgrades controlados.

### cordon — Marcar como no programable

Impide que nuevos pods sean programados en el nodo, pero **no mueve** los pods existentes.

```bash
kubectl cordon <node-name>

# Verificar: el nodo aparecerá como SchedulingDisabled
kubectl get nodes
```

**Cuándo usarlo:** Antes de aplicar parches del SO, reinicios planificados o antes de `drain` si quieres asegurarte de que nada nuevo aterrice mientras preparas el nodo.

### drain — Evacuar un nodo

Combina `cordon` + expulsión segura de todos los pods del nodo.

```bash
kubectl drain <node-name> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=30 \
  --timeout=120s
```

| Flag | Descripción |
|------|-------------|
| `--ignore-daemonsets` | No intenta mover pods de DaemonSets (no se pueden mover) |
| `--delete-emptydir-data` | Acepta eliminar datos de volúmenes emptyDir |
| `--grace-period` | Segundos para que los pods terminen limpiamente |
| `--timeout` | Tiempo máximo antes de forzar la operación |
| `--force` | Elimina pods que no tienen un controlador (stateless sueltos) |

> ⚠️ Si un nodo tiene pods con PodDisruptionBudgets muy restrictivos, `drain` puede quedar en espera. Revisa con `kubectl get pdb -A`.

### uncordon — Reactivar el nodo

Vuelve a marcar el nodo como programable.

```bash
kubectl uncordon <node-name>
```

### Resumen visual

```
Estado normal:  [Node: Ready]
     ↓ cordon
Estado cordoned: [Node: Ready,SchedulingDisabled]  ← no recibe pods nuevos
     ↓ drain
Estado drenado: [Node: Ready,SchedulingDisabled]  ← sin pods (excepto daemonsets)
     ↓ mantenimiento / upgrade
     ↓ uncordon
Estado normal:  [Node: Ready]
```

---

## etcd: Backups y Restore

### ¿Qué es etcd?

etcd es una base de datos distribuida clave-valor que almacena **todo el estado del cluster de Kubernetes**:

- Definiciones de objetos (Pods, Deployments, Services, ConfigMaps, Secrets…)
- Estado actual del cluster
- Configuración de RBAC

> Si pierdes etcd y no tienes backup, **pierdes el cluster completo**. Sus datos son irreemplazables.

### Dónde vive etcd

En clusters creados con `kubeadm`, etcd corre como un **Static Pod** en el nodo control plane:

```bash
# Ver el pod de etcd
kubectl get pods -n kube-system | grep etcd

# Ver la configuración del static pod
cat /etc/kubernetes/manifests/etcd.yaml
```

Los parámetros más importantes del manifest de etcd:

```yaml
# Fragmento relevante de /etc/kubernetes/manifests/etcd.yaml
spec:
  containers:
  - command:
    - etcd
    - --advertise-client-urls=https://192.168.1.100:2379
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --data-dir=/var/lib/etcd          # ← donde están los datos
    - --listen-client-urls=https://127.0.0.1:2379,https://192.168.1.100:2379
```

### Herramienta: etcdctl

`etcdctl` es la CLI oficial de etcd. Siempre se usa con `ETCDCTL_API=3`:

```bash
# Verificar que está disponible
etcdctl version

# Forma recomendada: exportar la variable de entorno
export ETCDCTL_API=3
```

---

### Backup de etcd

#### Identificar los certificados necesarios

Todos los comandos de etcdctl requieren autenticación TLS. Los certificados están en:

```
/etc/kubernetes/pki/etcd/
├── ca.crt          # CA de etcd
├── server.crt      # Certificado del servidor
├── server.key      # Clave del servidor
├── peer.crt
└── peer.key
```

Para backups (cliente → servidor), se usan:
- `--cacert`: `/etc/kubernetes/pki/etcd/ca.crt`
- `--cert`: `/etc/kubernetes/pki/etcd/server.crt`
- `--key`: `/etc/kubernetes/pki/etcd/server.key`

#### Verificar conectividad con etcd

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

Salida esperada:
```
https://127.0.0.1:2379 is healthy: successfully committed proposal: took = 2.5ms
```

#### Crear el snapshot

```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /opt/backup/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db
```

#### Verificar el snapshot

```bash
ETCDCTL_API=3 etcdctl \
  snapshot status /opt/backup/etcd-snapshot-20240315-120000.db \
  --write-out=table
```

Salida esperada:
```
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| a7d1c3b4 |    12345 |       1203 |     4.2 MB |
+----------+----------+------------+------------+
```

#### Script de backup automatizado

```bash
#!/bin/bash
# /opt/scripts/etcd-backup.sh

BACKUP_DIR="/opt/etcd-backups"
DATE=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_FILE="$BACKUP_DIR/etcd-snapshot-$DATE.db"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save "$SNAPSHOT_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Backup guardado en: $SNAPSHOT_FILE"
  # Eliminar backups más antiguos que RETENTION_DAYS días
  find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
  echo "🗑️  Backups antiguos (>${RETENTION_DAYS}d) eliminados"
else
  echo "❌ Error al crear el backup"
  exit 1
fi
```

```bash
# Programar con cron (cada día a las 2:00 AM)
crontab -e
# Añadir:
0 2 * * * /opt/scripts/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

---

### Restore de etcd

> ⚠️ **El restore de etcd es una operación crítica**. Detiene temporalmente el cluster. Planifícalo con cuidado.

#### Flujo del restore

```
1. Detener el API Server (para evitar escrituras durante el restore)
2. Restaurar el snapshot a un nuevo directorio
3. Actualizar etcd para que use el nuevo directorio
4. Reiniciar etcd (y el API Server)
5. Verificar el estado del cluster
```

#### Paso 1: Detener el API Server

En clusters kubeadm, los componentes del control plane son **Static Pods**. Para pararlos, mueve sus manifiestos fuera del directorio watched por kubelet:

```bash
# Hacer backup de los manifiestos
mkdir -p /tmp/k8s-manifests-backup
cp /etc/kubernetes/manifests/*.yaml /tmp/k8s-manifests-backup/

# Mover el manifest del API server fuera del directorio vigilado
mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
# (opcional: también etcd si quieres pararlo explícitamente)
mv /etc/kubernetes/manifests/etcd.yaml /tmp/

# Esperar a que los pods se paren (puede tardar ~30s)
watch crictl pods
```

#### Paso 2: Restaurar el snapshot

```bash
ETCDCTL_API=3 etcdctl \
  snapshot restore /opt/backup/etcd-snapshot-20240315-120000.db \
  --data-dir=/var/lib/etcd-restored \
  --name=master \
  --initial-cluster=master=https://127.0.0.1:2380 \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://127.0.0.1:2380
```

| Flag | Descripción |
|------|-------------|
| `--data-dir` | Nuevo directorio donde se restauran los datos |
| `--name` | Nombre del miembro etcd (ver en el manifest original) |
| `--initial-cluster` | Lista de peers (ver en el manifest original) |
| `--initial-cluster-token` | Token único para el nuevo cluster |
| `--initial-advertise-peer-urls` | URL de peer (ver en el manifest original) |

> 💡 Los valores de `--name`, `--initial-cluster` e `--initial-advertise-peer-urls` los encuentras en `/etc/kubernetes/manifests/etcd.yaml` (o en `/tmp/etcd.yaml` si lo moviste).

#### Paso 3: Actualizar el manifest de etcd

Edita el manifest de etcd para apuntar al nuevo directorio de datos:

```bash
# Si usas vim
vim /tmp/etcd.yaml
```

Cambia:
```yaml
# ANTES
  volumes:
  - hostPath:
      path: /var/lib/etcd        # ← directorio original
      type: DirectoryOrCreate
    name: etcd-data

# DESPUÉS
  volumes:
  - hostPath:
      path: /var/lib/etcd-restored    # ← nuevo directorio
      type: DirectoryOrCreate
    name: etcd-data
```

También necesitas actualizar el `--data-dir` en los args del container:

```yaml
# ANTES
    - --data-dir=/var/lib/etcd

# DESPUÉS
    - --data-dir=/var/lib/etcd-restored
```

#### Paso 4: Restaurar los manifiestos y reiniciar

```bash
# Volver a poner etcd y el API server en el directorio vigilado
mv /tmp/etcd.yaml /etc/kubernetes/manifests/
mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/

# kubelet detectará los cambios y levantará los pods automáticamente
# Esperar hasta que los pods estén Running
watch kubectl get pods -n kube-system
```

#### Paso 5: Verificar el restore

```bash
# Verificar que el cluster responde
kubectl get nodes
kubectl get pods -A

# Verificar que los datos se han restaurado
kubectl get deployments -A
kubectl get services -A
```

#### Alternativa: Cambiar ownership del directorio restaurado

Si etcd no puede leer el directorio restaurado por permisos:

```bash
# etcd corre como usuario root (uid/gid depende de la instalación)
chown -R etcd:etcd /var/lib/etcd-restored
# O bien:
chmod 700 /var/lib/etcd-restored
```

---

## Velero: Backup a Nivel de Cluster

### ¿Por qué Velero?

`etcdctl snapshot` hace un backup **de bajo nivel** del estado completo de etcd. Es perfecto para disaster recovery total pero tiene limitaciones:

| Característica | etcdctl snapshot | Velero |
|---|---|---|
| Granularidad | Todo o nada | Namespace, label, recurso específico |
| Backup de volúmenes (PVs) | ❌ No | ✅ Sí (con plugins de CSI o Restic) |
| Restore en cluster diferente | ⚠️ Complejo | ✅ Nativo |
| Programación de backups | Manual/cron | ✅ Integrado |
| Interfaz | CLI etcdctl | kubectl + CLI velero |
| Migración entre clusters | ❌ No | ✅ Sí |
| Open Source | ✅ | ✅ (CNCF) |

**Velero** (antes Heptio Ark) es el estándar de facto en la industria para backups de Kubernetes a nivel de recursos. Es mantenido por VMware y forma parte del ecosistema CNCF.

---

### Instalación

#### Prerequisitos

- Acceso a un almacenamiento de objetos: AWS S3, GCS, Azure Blob, MinIO (on-prem)
- CLI `velero` instalada
- `kubectl` configurado contra el cluster objetivo

#### Instalar la CLI

```bash
# Linux (x86_64)
VELERO_VERSION="v1.13.0"
curl -L "https://github.com/vmware-tanzu/velero/releases/download/${VELERO_VERSION}/velero-${VELERO_VERSION}-linux-amd64.tar.gz" | tar xz
sudo mv velero-*/velero /usr/local/bin/
velero version --client-only
```

#### Instalar Velero en el cluster (ejemplo con MinIO/S3)

Primero, crea un archivo de credenciales:

```bash
cat > /tmp/credentials-velero << EOF
[default]
aws_access_key_id=minioadmin
aws_secret_access_key=minioadmin
EOF
```

Instalar con el proveedor de AWS/S3:

```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.9.0 \
  --bucket velero-backups \
  --secret-file /tmp/credentials-velero \
  --use-volume-snapshots=false \
  --backup-location-config \
    region=minio,s3ForcePathStyle=true,s3Url=http://minio.example.com:9000

# Verificar instalación
kubectl get pods -n velero
velero backup-location get
```

#### Instalar con soporte de volúmenes (Restic/Kopia)

Para hacer backup de datos en PersistentVolumes:

```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.9.0 \
  --bucket velero-backups \
  --secret-file /tmp/credentials-velero \
  --use-node-agent \                        # Activa Restic/Kopia como DaemonSet
  --default-volumes-to-fs-backup \          # Backup de todos los volúmenes por defecto
  --backup-location-config \
    region=minio,s3ForcePathStyle=true,s3Url=http://minio.example.com:9000
```

---

### Crear un Backup

#### Backup completo del cluster

```bash
velero backup create cluster-backup-$(date +%Y%m%d) \
  --wait

# Ver el estado
velero backup describe cluster-backup-20240315
velero backup logs cluster-backup-20240315
```

#### Backup de un namespace específico

```bash
velero backup create backup-production \
  --include-namespaces production \
  --wait
```

#### Backup de múltiples namespaces

```bash
velero backup create backup-apps \
  --include-namespaces production,staging,monitoring \
  --wait
```

#### Backup por label selector

```bash
velero backup create backup-api \
  --selector app=api-gateway \
  --wait
```

#### Backup con TTL (Time to Live)

```bash
velero backup create backup-prod \
  --include-namespaces production \
  --ttl 720h \     # 30 días
  --wait
```

#### Backup incluyendo PersistentVolumes

```bash
# Con anotación en el pod (si no usas --default-volumes-to-fs-backup)
kubectl annotate pod <pod-name> \
  backup.velero.io/backup-volumes=<volume-name>

# O directamente en el backup
velero backup create backup-with-volumes \
  --include-namespaces production \
  --default-volumes-to-fs-backup \
  --wait
```

#### Listar backups

```bash
velero backup get

# Salida:
# NAME                        STATUS      ERRORS  CREATED                       TTL    STORAGE LOCATION
# cluster-backup-20240315     Completed   0       2024-03-15 12:00:00 +0000     720h   default
```

---

### Restore con Velero

#### Restore completo desde un backup

```bash
velero restore create \
  --from-backup cluster-backup-20240315 \
  --wait

# Ver el estado del restore
velero restore get
velero restore describe <restore-name>
```

#### Restore de namespace específico

```bash
velero restore create restore-production \
  --from-backup cluster-backup-20240315 \
  --include-namespaces production \
  --wait
```

#### Restore en un namespace diferente (remapping)

```bash
velero restore create restore-prod-to-staging \
  --from-backup backup-production \
  --namespace-mappings production:staging \
  --wait
```

> Útil para crear entornos de prueba a partir de producción, o migrar entre clusters.

#### Restore de recursos específicos

```bash
velero restore create restore-configmaps \
  --from-backup cluster-backup-20240315 \
  --include-resources configmaps,secrets \
  --include-namespaces production \
  --wait
```

#### Restore excluyendo recursos

```bash
velero restore create restore-no-hpa \
  --from-backup cluster-backup-20240315 \
  --exclude-resources horizontalpodautoscalers \
  --wait
```

---

### Schedules y Políticas

Velero tiene un sistema de schedules basado en sintaxis cron:

#### Crear un schedule

```bash
# Backup diario a las 2:00 AM con retención de 30 días
velero schedule create daily-cluster-backup \
  --schedule="0 2 * * *" \
  --ttl 720h \
  --include-namespaces production,staging

# Backup cada hora de un namespace crítico
velero schedule create hourly-database-backup \
  --schedule="0 * * * *" \
  --include-namespaces database \
  --ttl 48h
```

#### Gestionar schedules

```bash
# Listar schedules
velero schedule get

# Ver detalles
velero schedule describe daily-cluster-backup

# Lanzar un backup manual desde un schedule
velero backup create --from-schedule daily-cluster-backup

# Pausar un schedule
velero schedule patch daily-cluster-backup --paused true

# Eliminar un schedule
velero schedule delete daily-cluster-backup
```

#### Ejemplo de política de backups

```bash
# Backup completo semanal (domingos a las 1:00 AM) - 90 días de retención
velero schedule create weekly-full-backup \
  --schedule="0 1 * * 0" \
  --ttl 2160h   # 90 días

# Backup incremental diario (2:00 AM) - 14 días de retención
velero schedule create daily-incremental-backup \
  --schedule="0 2 * * 1-6" \
  --ttl 336h    # 14 días
  --include-namespaces production,staging,monitoring
```

---

## Otras Herramientas de Backup

Además de `etcdctl` y Velero, existen otras opciones en el ecosistema:

### Kasten K10 (Veeam)

- **Tipo**: Enterprise, freemium
- **Fuerte en**: Aplicaciones stateful, bases de datos (MongoDB, PostgreSQL, Cassandra)
- **UI**: Dashboard web muy completo
- **Cuándo usarlo**: Entornos enterprise con requisitos de compliance (GDPR, HIPAA)
- **Web**: [kasten.io](https://www.kasten.io)

### Trilio for Kubernetes (TrilioVault)

- **Tipo**: Enterprise
- **Fuerte en**: Backup application-aware, soporte multi-cloud
- **Cuándo usarlo**: Entornos híbridos con workloads complejos
- **Web**: [trilio.io](https://trilio.io)

### Longhorn (rancher/longhorn)

- **Tipo**: Open Source (CNCF Incubating)
- **Fuerte en**: Storage distribuido + snapshots de volúmenes
- **Nota**: Es un CSI driver + sistema de backup para PVs, no para recursos de Kubernetes
- **Web**: [longhorn.io](https://longhorn.io)

### Comparativa rápida

| Herramienta | Open Source | PV Backup | App-Aware | Curva de aprendizaje | CKA relevante |
|-------------|-------------|-----------|-----------|----------------------|---------------|
| etcdctl | ✅ | ❌ | ❌ | Baja | ✅ Sí |
| **Velero** | ✅ | ✅ | Parcial | Media | ⚠️ Extra |
| Kasten K10 | Freemium | ✅ | ✅ | Alta | ❌ No |
| TrilioVault | ❌ | ✅ | ✅ | Alta | ❌ No |
| Longhorn | ✅ | ✅ | ❌ | Media | ❌ No |

> **Conclusión**: Para el CKA, domina `etcdctl`. Para producción, Velero es el estándar más adoptado y el primer paso antes de evaluar herramientas enterprise.

---

## Cheatsheet para el Examen CKA

### Upgrade (Recordatorio rápido)

```bash
# 1. Actualizar kubeadm
apt-mark unhold kubeadm && apt-get install -y kubeadm=1.X.Y-1.1 && apt-mark hold kubeadm

# 2. Plan y apply en control plane
kubeadm upgrade plan
kubeadm upgrade apply v1.X.Y

# 3. Drenar nodo
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data

# 4. Actualizar kubelet y kubectl
apt-mark unhold kubelet kubectl
apt-get install -y kubelet=1.X.Y-1.1 kubectl=1.X.Y-1.1
apt-mark hold kubelet kubectl
systemctl daemon-reload && systemctl restart kubelet

# 5. Volver a poner en servicio
kubectl uncordon <node>
```

### etcd Backup

```bash
# Una sola línea para el examen
ETCDCTL_API=3 etcdctl snapshot save /opt/backup/etcd.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verificar
ETCDCTL_API=3 etcdctl snapshot status /opt/backup/etcd.db --write-out=table
```

### etcd Restore

```bash
# 1. Mover manifiestos (parar API server y etcd)
mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
mv /etc/kubernetes/manifests/etcd.yaml /tmp/

# 2. Restaurar
ETCDCTL_API=3 etcdctl snapshot restore /opt/backup/etcd.db \
  --data-dir=/var/lib/etcd-new

# 3. Editar /tmp/etcd.yaml: cambiar --data-dir y hostPath a /var/lib/etcd-new

# 4. Restaurar manifiestos
mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
mv /tmp/etcd.yaml /etc/kubernetes/manifests/

# 5. Esperar y verificar
kubectl get nodes
```

### Comandos de diagnóstico útiles

```bash
# Ver logs de etcd
kubectl logs -n kube-system etcd-<control-plane-node>

# Ver configuración actual de etcd
kubectl describe pod -n kube-system etcd-<control-plane-node>

# Listar todas las claves en etcd (útil para debugging)
ETCDCTL_API=3 etcdctl get / --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  | head -50

# Contar claves en etcd
ETCDCTL_API=3 etcdctl get / --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  | wc -l
```

---

*Guía preparada para el examen CKA · Kubernetes v1.29+ · kubeadm clusters*