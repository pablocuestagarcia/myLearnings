# Reporte de Estado y Decisiones Arquitectónicas: Integración GitHub -> n8n -> Azure Event Hub

**Rol:** Staff Software Engineer
**Contexto:** Construcción de un flujo automatizado para ingestar eventos de GitHub mediante webhooks en n8n y su posterior enrutamiento a Azure Event Hubs.

---

## 1. Estado Actual del Proyecto (Current Status)

### 🔴 Bloqueo Crítico: Comunicación GitHub -> n8n
Actualmente, no se ha logrado establecer comunicación exitosa entre el webhook de GitHub y el nodo de entrada (Webhook) de n8n. 

**Diagnóstico Inicial:**
- Las peticiones simuladas enviadas a la URL del webhook de n8n mediante **Postman resultan exitosas**, lo que confirma que el nodo de n8n está escuchando y procesando correctamente las peticiones HTTP externas.
- Sin embargo, las peticiones automatizadas lanzadas desde los eventos de GitHub no están llegando a n8n o están fallando en el proceso de entrega.

**Próximos pasos para investigación (Troubleshooting):**
1. **Revisar *Delivery Logs* en GitHub:** Ir a la configuración del repositorio en GitHub (`Settings` > `Webhooks`), seleccionar el webhook y analizar la pestaña *Recent Deliveries* para comprobar el código de error HTTP (ej. `Timeout`, `403`, `500`) y el cuerpo de la respuesta.
2. **Revisar conectividad de red:** Comprobar si existe un bloqueo por parte de firewalls, restricciones de red corporativa, o si n8n se encuentra en un entorno local (localhost) inaccesible desde internet (en cuyo caso se requerirá un túnel como `ngrok`).

---

## 2. Discusión de Seguridad y Arquitectura (Azure Event Hub)

El diseño de la arquitectura se ha centrado rigurosamente en cómo asegurar la conexión entre n8n y Azure Event Hub, evitando la exposición de secretos en código fuente (texto plano) y respetando el Principio de Menor Privilegio.

### 2.1. Entra ID (OAuth2) vs. Shared Access Signature (SAS)
Se han evaluado dos enfoques de autenticación en Azure:
- **Entra ID (Service Principal):** [Estándar Enterprise]. Emplea RBAC (Role-Based Access Control) mediante el rol de *Azure Event Hubs Data Sender*. Elimina la necesidad de rotar claves compartidas y ofrece trazabilidad absoluta.
- **SAS Tokens:** [Legacy / Alternativa]. Utiliza claves maestras (`KEY`) para firmar tokens temporalmente al vuelo mediante algoritmos de criptografía (`HMAC-SHA256`). Aceptable a nivel técnico, pero presenta mayores riesgos de exposición si la clave maestra no se resguarda correctamente.

### 2.2. Gestión de Secretos en n8n
Para la generación dinámica de tokens SAS, el desafío es cómo inyectar la clave maestra (`KEY`) en el nodo "Code" de n8n de forma segura. Las opciones analizadas fueron:

1. ❌ **Variables Nativas de n8n:** Descartadas, dado que la versión Community instalada restringe el uso de este panel global de variables.
2. ❌ **Variables de Entorno Docker (`$env`):** Una solución robusta, gratuita y altamente recomendada a medio plazo. Permite inyectar secretos a nivel de orquestador de contenedores. **Descartada a corto plazo** por la falta de acceso y control inmediato sobre el contenedor subyacente de n8n.
3. ❌ **Credenciales "Dummy" (Basic Auth):** Descartado por ser un anti-patrón que dificulta la legibilidad, mantenimiento y portabilidad del código.
4. ✅ **Azure Key Vault (Arquitectura Seleccionada):** La estrategia a seguir consistirá en integrar n8n directamente con Azure Key Vault. El flujo realizará una llamada para obtener el secreto en tiempo real justo antes de firmar el token SAS. Esto garantiza un almacenamiento seguro, centralizado y acorde a los más altos estándares de Cloud Security.

---

## 3. Anexos de Código Base

A continuación se documenta el código CommonJS y Python construido para la generación de tokens SAS, listo para implementarse en el nodo "Code" una vez se resuelva la integración con Azure Key Vault.

### Generador SAS en Node.js (CommonJS)

```javascript
// Requiere habilitar NODE_FUNCTION_ALLOW_BUILTIN=* en el entorno de n8n
const crypto = require("crypto");

// TODO: Estos valores se obtendrán dinámicamente de Key Vault en nodos previos
const NAMESPACE = "tu-namespace";
const EVENTHUB  = "tu-eventhub";
const KEY_NAME  = "tu-key-name";
const KEY       = "SECRETO_EXTRAIDO_DE_KEY_VAULT"; 

// Generar tiempo de expiración (24 horas)
const expiry = Math.floor(Date.now() / 1000) + 86400;
const uri    = `https://${NAMESPACE}.servicebus.windows.net/${EVENTHUB}`;

// Firmar la petición
const sts    = encodeURIComponent(uri) + "\n" + expiry;
const sig    = crypto.createHmac("sha256", KEY).update(sts).digest("base64");

// Ensamblar token final
const token  = `SharedAccessSignature sr=${encodeURIComponent(uri)}&sig=${encodeURIComponent(sig)}&se=${expiry}&skn=${KEY_NAME}`;

// Devolver el token inyectado en el payload para el nodo HTTP Request
for (const item of $input.all()) {
  item.json.sasToken = token;
}
return $input.all();
```

### Generador SAS en Python (Pyodide)

```python
import hmac, hashlib, base64, urllib.parse, time

# TODO: Estos valores se obtendrán dinámicamente de Key Vault
NAMESPACE = "tu-namespace"
EVENTHUB  = "tu-eventhub"
KEY_NAME  = "tu-key-name"
KEY       = "SECRETO_EXTRAIDO_DE_KEY_VAULT"

expiry = int(time.time()) + 86400
uri    = f"https://{NAMESPACE}.servicebus.windows.net/{EVENTHUB}"

# Firmar la petición
sts    = urllib.parse.quote_plus(uri) + "\n" + str(expiry)
sig    = base64.b64encode(hmac.new(KEY.encode(), sts.encode(), hashlib.sha256).digest()).decode('utf-8')

# Ensamblar token final
token  = f"SharedAccessSignature sr={urllib.parse.quote_plus(uri)}&sig={urllib.parse.quote_plus(sig)}&se={expiry}&skn={KEY_NAME}"

# Devolver el token inyectado
return_items = []
for item in _input.all():
    item.json['sasToken'] = token
    return_items.append({"json": item.json})

return return_items
```
