# Admission Controllers en Kubernetes — Nota de estudio para CKA

> Plugins que interceptan peticiones al `kube-apiserver` **después** de autenticación y autorización, y **antes** de persistir en `etcd`. Permiten validar, mutar o ambas cosas sobre el objeto.

---

## 1. Teoría fundamental

### 1.1. Posición en el flujo del API Server

```
Cliente (kubectl/SDK)
   │
   ▼
[ Autenticación ]   ¿Quién eres?
   │
   ▼
[ Autorización (RBAC/ABAC/Node) ]   ¿Puedes hacer esto?
   │
   ▼
[ Mutating Admission Controllers ]   Modifican el objeto
   │
   ▼
[ Object Schema Validation ]   Validación OpenAPI
   │
   ▼
[ Validating Admission Controllers ]   Aceptan o rechazan
   │
   ▼
[ etcd ]   Persistencia
```

Punto clave para el examen: **autenticación y autorización NO son admission controllers**. Los admission controllers actúan después, sobre el contenido del objeto.

### 1.2. Tipos

| Tipo | Qué hace | Ejemplos built-in |
|---|---|---|
| **Mutating** | Modifica el objeto antes de persistirlo (añade defaults, labels, sidecars, etc.) | `DefaultStorageClass`, `ServiceAccount`, `MutatingAdmissionWebhook` |
| **Validating** | Acepta o rechaza la petición sin modificarla | `NamespaceLifecycle`, `ResourceQuota`, `ValidatingAdmissionWebhook` |

Algunos controllers son **ambos** (p. ej. `PodSecurity`, `ResourceQuota`).

### 1.3. Orden de ejecución

1. **Primero los mutating**, en orden alfabético del nombre del webhook (los built-in siguen un orden interno).
2. **Después los validating**, en paralelo.

Razón: cualquier cambio aplicado por mutating debe poder ser validado después. Si fuese al revés, una validación podría aceptar algo que un mutating posterior rompería.

### 1.4. Casos de rechazo

Si **cualquier** admission controller rechaza la petición, esta se aborta y se devuelve el error al cliente. No hay "consenso por mayoría": basta un veto.

---

## 2. Admission Controllers built-in clave para CKA

| Plugin | Tipo | Función |
|---|---|---|
| `NamespaceLifecycle` | Validating | Impide crear objetos en namespaces inexistentes o en fase `Terminating`. Protege `default`, `kube-system`, `kube-public`. |
| `LimitRanger` | Mutating + Validating | Aplica defaults/limites de `LimitRange`. |
| `ResourceQuota` | Validating | Aplica los `ResourceQuota` del namespace. Debe ir al final de la cadena de mutating. |
| `ServiceAccount` | Mutating | Asigna SA `default` y monta token automáticamente. |
| `DefaultStorageClass` | Mutating | Asigna la `StorageClass` marcada como default a PVCs sin `storageClassName`. |
| `DefaultIngressClass` | Mutating | Equivalente al anterior para Ingress. |
| `NodeRestriction` | Validating | Restringe lo que un kubelet puede modificar (solo sus propios Node/Pod). **Crítico** para seguridad. |
| `PodSecurity` | Validating | Enforcement de Pod Security Standards (sustituyó a `PodSecurityPolicy` en 1.25). |
| `MutatingAdmissionWebhook` | Mutating | Llama a webhooks externos para mutar. |
| `ValidatingAdmissionWebhook` | Validating | Llama a webhooks externos para validar. |
| `AlwaysPullImages` | Mutating | Fuerza `imagePullPolicy: Always` (evita que pods accedan a imágenes cacheadas sin autorización). |
| `EventRateLimit` | Validating | Limita el ratio de creación de eventos. |
| `PersistentVolumeClaimResize` | Validating | Habilita el resize de PVCs. |

---

## 3. Configuración del kube-apiserver

### 3.1. Flags principales

```bash
--enable-admission-plugins=NodeRestriction,PodSecurity,ResourceQuota,ServiceAccount
--disable-admission-plugins=AlwaysAdmit
--admission-control-config-file=/etc/kubernetes/admission-config.yaml
```

> En Kubernetes moderno **no hay que listar todos** los plugins: los recomendados están habilitados por defecto. Solo se añaden los extra o se desactivan los no deseados.

### 3.2. Cómo inspeccionarlo (típico en CKA)

**Cluster con kubeadm:**

```bash
# Manifest estático del API server
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep admission

# Plugins habilitados por defecto en esta versión
kube-apiserver -h | grep enable-admission-plugins
```

**Modificar:** editar el manifest del API server. Como es un static pod, kubelet lo reinicia automáticamente al guardar.

```bash
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Añadir/modificar la línea:
#   - --enable-admission-plugins=NodeRestriction,PodSecurity
```

### 3.3. AdmissionConfiguration file

Para configurar plugins que requieren parámetros (p. ej. `PodSecurity`, `EventRateLimit`):

```yaml
# /etc/kubernetes/admission-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: PodSecurity
  configuration:
    apiVersion: pod-security.admission.config.k8s.io/v1
    kind: PodSecurityConfiguration
    defaults:
      enforce: "restricted"
      enforce-version: "latest"
      audit: "restricted"
      warn: "restricted"
    exemptions:
      usernames: []
      runtimeClasses: []
      namespaces: ["kube-system"]
- name: EventRateLimit
  path: /etc/kubernetes/eventconfig.yaml
```

Y referenciarlo en el kube-apiserver:

```yaml
- --admission-control-config-file=/etc/kubernetes/admission-config.yaml
```

---

## 4. Dynamic Admission Control: Webhooks

Para lógica personalizada sin recompilar Kubernetes. Dos tipos:

- `MutatingWebhookConfiguration`
- `ValidatingWebhookConfiguration`

### 4.1. Flujo

```
API Server  ──▶  POST /mutate (AdmissionReview JSON)  ──▶  Webhook Server
            ◀──  AdmissionReview response (allowed, patch)
```

El `AdmissionReview` contiene: `uid`, `user`, `operation` (CREATE/UPDATE/DELETE/CONNECT), `kind`, `resource`, `namespace`, `object`, `oldObject` (en UPDATE), `dryRun`.

### 4.2. Despliegue del webhook server

Pasos:
1. Programar servidor HTTPS que acepte `/mutate` y `/validate`.
2. Containerizarlo y desplegarlo como `Deployment` + `Service` en el cluster (o externo via URL).
3. Generar certificado TLS firmado por una CA (cert-manager es lo habitual).
4. Crear el `WebhookConfiguration` con el `caBundle`.

### 4.3. MutatingWebhookConfiguration completa

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
- name: pod-policy.example.com
  clientConfig:
    service:
      namespace: webhook-system
      name: webhook-service
      path: /mutate
      port: 443
    caBundle: <BASE64-CA-CERT>
    # Alternativa para webhook externo al cluster:
    # url: "https://my-webhook.example.com:9443/mutate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
    scope: "Namespaced"
  failurePolicy: Fail
  matchPolicy: Equivalent
  sideEffects: None
  admissionReviewVersions: ["v1"]
  timeoutSeconds: 5
  reinvocationPolicy: IfNeeded
  namespaceSelector:
    matchExpressions:
    - key: webhook
      operator: NotIn
      values: ["disabled"]
  objectSelector:
    matchExpressions:
    - key: skip-webhook
      operator: DoesNotExist
```

### 4.4. Campos críticos

| Campo | Valores | Cuándo usar cada uno |
|---|---|---|
| `failurePolicy` | `Fail` / `Ignore` | `Fail` = seguridad estricta pero riesgo de romper el cluster si el webhook cae. `Ignore` = pragmático, recomendado para webhooks de "mejora". |
| `matchPolicy` | `Exact` / `Equivalent` | `Equivalent` (default) matchea también versiones equivalentes del recurso vía conversión. |
| `sideEffects` | `None`, `NoneOnDryRun`, `Some`, `Unknown` | `None` es lo correcto si el webhook no toca recursos externos. Requerido en v1. |
| `reinvocationPolicy` | `Never`, `IfNeeded` | `IfNeeded` re-invoca el webhook si otro mutating posterior modificó el objeto. Tu webhook **debe ser idempotente**. |
| `timeoutSeconds` | 1-30 | Mantén bajo (5-10s). Timeouts altos degradan el API server. |
| `admissionReviewVersions` | Lista | `["v1"]` es el estándar actual. |
| `namespaceSelector` | LabelSelector | Filtra por labels del namespace. **Imprescindible para excluir `kube-system`.** |
| `objectSelector` | LabelSelector | Filtra por labels del propio objeto. |

### 4.5. Respuesta esperada del webhook

**Validating:**

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<request-uid>",
    "allowed": false,
    "status": {
      "code": 403,
      "message": "Imagen no permitida"
    }
  }
}
```

**Mutating** (con JSON Patch RFC 6902 en base64):

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<request-uid>",
    "allowed": true,
    "patchType": "JSONPatch",
    "patch": "W3sib3AiOiJhZGQiLCJwYXRoIjoiL21ldGFkYXRhL2xhYmVscy9hZGRlZCIsInZhbHVlIjoidHJ1ZSJ9XQ=="
  }
}
```

El patch decodificado es algo como:

```json
[{"op":"add","path":"/metadata/labels/added","value":"true"}]
```

---

## 5. ValidatingAdmissionPolicy (CEL, GA en 1.30)

Alternativa **moderna sin webhook externo**: políticas declarativas usando CEL (Common Expression Language). Ideal cuando no necesitas mutación.

### Ejemplo: limitar replicas de Deployments

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: replica-limit-policy
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups:   ["apps"]
      apiVersions: ["v1"]
      operations:  ["CREATE", "UPDATE"]
      resources:   ["deployments"]
  validations:
  - expression: "object.spec.replicas <= 5"
    message: "Las replicas no pueden ser > 5"
    reason: Invalid
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: replica-limit-binding
spec:
  policyName: replica-limit-policy
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchLabels:
        environment: production
```

Ventajas frente a webhooks: sin servidor que mantener, sin certificados, menor latencia, menos puntos de fallo.

---

## 6. Herramientas reales: Kyverno y OPA Gatekeeper

En producción casi nadie escribe webhooks desde cero. Se usan:

| Herramienta | Lenguaje de políticas | Notas |
|---|---|---|
| **Kyverno** | YAML nativo de K8s | Más fácil de adoptar. Soporta validate, mutate y generate. |
| **OPA Gatekeeper** | Rego | Más potente pero curva más empinada. Estándar CNCF. |

Ambos se instalan como webhook con sus propios CRDs (`ClusterPolicy`, `ConstraintTemplate`, etc.) y traducen las políticas a llamadas de admission.

---

## 7. Caso real complejo: Multi-tenant con compliance

### 7.1. Escenario

Cluster compartido entre 3 equipos. El equipo de plataforma necesita garantizar:

1. **Solo imágenes** de `registry.corp.example.com` o `gcr.io/our-project`.
2. **Pods sin `resources.limits`** se rechazan… excepto en namespaces con label `auto-limits=true`, donde se **inyectan automáticamente** desde una baseline.
3. Todo pod debe tener label `cost-center` que **coincida** con el label del namespace.
4. Pods de tenants deben tener `nodeSelector` que los anclen a nodos del tenant.
5. El webhook **NO** debe aplicar a `kube-system` ni a sí mismo (evitar deadlocks).

### 7.2. Arquitectura

```
        ┌──────────────────────────────────────────┐
        │            kube-apiserver                │
        └─────┬────────────────────────┬───────────┘
              │ mutate                 │ validate
              ▼                        ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ MutatingWebhook  │    │ValidatingWebhook │
    │  /mutate-pods    │    │  /validate-pods  │
    └────────┬─────────┘    └────────┬─────────┘
             └──────────┬────────────┘
                        ▼
              ┌──────────────────┐
              │ policy-webhook   │  ← Deployment + Service
              │  (HTTPS)         │     en ns platform-system
              └──────────────────┘
```

### 7.3. Configuración del MutatingWebhook

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-defaults.platform.io
webhooks:
- name: inject-defaults.platform.io
  clientConfig:
    service:
      namespace: platform-system
      name: policy-webhook
      path: /mutate-pods
      port: 443
    caBundle: <CA>
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  failurePolicy: Fail
  sideEffects: None
  admissionReviewVersions: ["v1"]
  timeoutSeconds: 5
  reinvocationPolicy: IfNeeded
  namespaceSelector:
    matchExpressions:
    - key: tenant
      operator: Exists
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system","platform-system"]
```

### 7.4. Configuración del ValidatingWebhook

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-compliance.platform.io
webhooks:
- name: validate-compliance.platform.io
  clientConfig:
    service:
      namespace: platform-system
      name: policy-webhook
      path: /validate-pods
      port: 443
    caBundle: <CA>
  rules:
  - operations: ["CREATE","UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  failurePolicy: Fail
  sideEffects: None
  admissionReviewVersions: ["v1"]
  timeoutSeconds: 5
  namespaceSelector:
    matchExpressions:
    - key: tenant
      operator: Exists
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system","platform-system"]
```

### 7.5. Pseudocódigo del servidor (mutación)

```python
@app.route('/mutate-pods', methods=['POST'])
def mutate_pods():
    req = request.json['request']
    pod = req['object']
    namespace = req['namespace']

    ns = k8s.read_namespace(namespace)
    tenant      = ns.metadata.labels.get('tenant')
    cost_center = ns.metadata.labels.get('cost-center')
    auto_limits = ns.metadata.labels.get('auto-limits') == 'true'

    patches = []

    # 1. nodeSelector según tenant
    patches.append({
        "op": "add",
        "path": "/spec/nodeSelector",
        "value": {"tenant": tenant}
    })

    # 2. Inyectar limits si auto-limits=true y faltan
    if auto_limits:
        for i, c in enumerate(pod['spec']['containers']):
            if not c.get('resources', {}).get('limits'):
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{i}/resources",
                    "value": {
                        "limits":   {"cpu": "500m", "memory": "512Mi"},
                        "requests": {"cpu": "100m", "memory": "128Mi"}
                    }
                })

    # 3. Inyectar label cost-center (idempotente)
    if not pod.get('metadata', {}).get('labels'):
        patches.append({"op": "add", "path": "/metadata/labels", "value": {}})
    patches.append({
        "op": "add",
        "path": "/metadata/labels/cost-center",
        "value": cost_center
    })

    return admission_response(req['uid'], allowed=True, patches=patches)
```

### 7.6. Pseudocódigo del servidor (validación)

```python
ALLOWED_REGISTRIES = ['registry.corp.example.com/', 'gcr.io/our-project/']

@app.route('/validate-pods', methods=['POST'])
def validate_pods():
    req = request.json['request']
    pod = req['object']
    namespace = req['namespace']
    ns = k8s.read_namespace(namespace)

    # 1. Validar registries
    for c in pod['spec']['containers']:
        if not any(c['image'].startswith(r) for r in ALLOWED_REGISTRIES):
            return reject(req['uid'], f"Image {c['image']} not from allowed registry")

    # 2. Validar limits presentes (si no es auto-limits=true)
    if ns.metadata.labels.get('auto-limits') != 'true':
        for c in pod['spec']['containers']:
            if not c.get('resources', {}).get('limits'):
                return reject(req['uid'], f"Container {c['name']} requires resources.limits")

    # 3. Validar cost-center match
    pod_cc = pod.get('metadata', {}).get('labels', {}).get('cost-center')
    ns_cc  = ns.metadata.labels.get('cost-center')
    if pod_cc != ns_cc:
        return reject(req['uid'], f"cost-center label mismatch: pod={pod_cc} ns={ns_cc}")

    return allow(req['uid'])
```

### 7.7. Por qué este diseño funciona y resuelve cada problema

| Problema | Solución |
|---|---|
| Mutating debe correr antes que validating | El orden interno de Kubernetes lo garantiza: el `cost-center` inyectado en mutating es validado por el validating sin que el usuario tenga que ponerlo. |
| Idempotencia ante `reinvocationPolicy: IfNeeded` | Los patches usan `add` sobre paths concretos; si ya existe el label/resources, el segundo pase produce el mismo resultado. |
| Deadlock si el webhook cae con `failurePolicy: Fail` | El `namespaceSelector` excluye `platform-system` y `kube-system`, por lo que el propio webhook puede arrancarse sin pasar por sí mismo. |
| Bypass por usuarios privilegiados | El webhook **no** depende del usuario; mira el objeto. Pero RBAC adicional debería impedir crear pods directamente fuera de Deployments. |
| Recursos cluster-scope no protegidos | Solo aplica a `pods` namespaced; si quisiéramos proteger CRDs cluster-scope, añadir más rules. |

### 7.8. Gotchas reales en producción

1. **Webhook en `kube-system`**: NUNCA poner el webhook en `kube-system` ni hacer que aplique sobre `kube-system`. Bloquearías kube-proxy, CoreDNS, etc.
2. **failurePolicy: Fail + webhook caído = cluster bloqueado** para los recursos afectados. Mitigar con HA (≥2 réplicas) + `PodDisruptionBudget` + exclusión cuidadosa de namespaces de sistema.
3. **Rotación de certificados**: usar `cert-manager` con un `Issuer` self-signed o el CA del cluster. El `caBundle` del WebhookConfiguration debe regenerarse en la rotación.
4. **timeoutSeconds bajos**: cada milisegundo cuenta en cada CREATE/UPDATE. Optimizar acceso a `read_namespace` con un informer cache.
5. **Logs y observabilidad**: instrumentar latencias, ratios de mutate/validate/reject. Sin esto, debuggear es un infierno.
6. **dryRun**: si tu webhook tiene side effects, debes implementar `sideEffects: NoneOnDryRun` y respetar `request.dryRun=true` (no hacer cambios externos).
7. **Update vs Create**: en UPDATE tienes `oldObject` disponible; útil para validar que ciertos campos no cambian (p. ej. `cost-center` immutable después de creado).

---

## 8. Comandos útiles para el examen CKA

```bash
# Ver admission plugins activos
ps -ef | grep kube-apiserver | grep -oP 'admission-plugins=\S+'

# o en kubeadm
grep -i admission /etc/kubernetes/manifests/kube-apiserver.yaml

# Ver webhooks configurados
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations
kubectl describe validatingwebhookconfiguration <nombre>

# Ver políticas modernas (CEL)
kubectl get validatingadmissionpolicies
kubectl get validatingadmissionpolicybindings

# Ver eventos de rechazo
kubectl get events --field-selector reason=FailedCreate
kubectl get events -A | grep -i admission

# Inspeccionar el patch aplicado por un mutating webhook
kubectl get pod <pod> -o yaml   # comparar con el manifest original

# Forzar reload del kube-apiserver tras editar el manifest
sudo systemctl restart kubelet  # kubelet vigila el manifest, no es necesario en general
```

---

## 9. Checklist mental para el CKA

- [ ] ¿Sé en qué orden van auth → authz → mutating → schema → validating?
- [ ] ¿Sé dónde editar los plugins habilitados? (`/etc/kubernetes/manifests/kube-apiserver.yaml`)
- [ ] ¿Sé qué hace cada uno de los 6-7 plugins built-in más importantes?
- [ ] ¿Sé la diferencia entre `MutatingWebhookConfiguration` y `ValidatingWebhookConfiguration`?
- [ ] ¿Sé qué es `failurePolicy` y por qué importa?
- [ ] ¿Sé identificar un cluster donde un webhook está bloqueando creaciones por estar caído?
- [ ] ¿Sé qué es `ValidatingAdmissionPolicy` y cuándo lo elegiría sobre un webhook?

---

## 10. Pitfalls típicos en preguntas de examen

1. Te piden activar un plugin pero olvidas que el API server hay que **reiniciarlo** (kubelet lo hace solo si editas el manifest).
2. Confundes orden: el examen puede preguntar **qué pasa primero**, mutating o validating. **Mutating.**
3. Crees que admission controllers controlan **acceso** (eso es authz). Controlan **contenido**.
4. Olvidas que `NamespaceLifecycle` impide eliminar `default`, `kube-system`, `kube-public`.
5. No relacionas `LimitRange` + `ResourceQuota` con admission controllers: ambos son enforced por admission.

---

**Recurso oficial:**
https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/
https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/