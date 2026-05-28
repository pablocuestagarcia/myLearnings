# Procesar Webhooks de GitHub y Enviar a Azure Event Hubs en n8n

Este documento detalla dos enfoques (JavaScript y Python) para analizar el cuerpo de un Webhook proveniente de GitHub (por ejemplo, un evento `push`) y posteriormente enviarlo a **Azure Event Hubs** mediante una petición HTTP.

En n8n, la arquitectura recomendada para este flujo consta de 3 nodos:
1. **Webhook Node:** Recibe el evento de GitHub.
2. **Code Node (JS o Python):** Analiza y transforma el payload.
3. **HTTP Request Node:** Se encarga de enviar los datos procesados de forma segura a Azure Event Hub.

A continuación, se presentan las opciones para el **Nodo de Código (Code Node)**.

---

## Opción 1: Usando JavaScript (Node.js nativo)

JavaScript es el lenguaje nativo de n8n. El siguiente código analiza la carga útil del webhook, extrae información relevante (quién hizo el push, qué repositorio, cuántos commits) y prepara el objeto para enviarlo a Azure.

### Código para el nodo "Code" (JavaScript)

```javascript
// Iteramos sobre todos los items de entrada que llegaron del Webhook
const returnItems = [];

for (const item of $input.all()) {
  // El payload del webhook de GitHub suele venir en la propiedad body
  const body = item.json.body || item.json;

  // Analizamos el contenido (ejemplo para un evento 'push')
  const repoName = body.repository ? body.repository.name : "Desconocido";
  const pusherName = body.pusher ? body.pusher.name : "Desconocido";
  const commits = body.commits ? body.commits.length : 0;
  
  let actionMessage = "Evento sin identificar";
  if (body.head_commit) {
    actionMessage = body.head_commit.message;
  }

  // Estructuramos los datos limpios que queremos enviar a Azure Event Hub
  const analyzedData = {
    source: "github_webhook",
    event_type: "push",
    repository: repoName,
    user: pusherName,
    total_commits: commits,
    latest_commit_message: actionMessage,
    timestamp: new Date().toISOString()
  };

  // Retornamos el nuevo objeto para el siguiente nodo
  returnItems.push({ json: analyzedData });
}

return returnItems;
```

---

## Opción 2: Usando Python (Pyodide)

Si prefieres usar Python, asegúrate de que tu nodo **Code** esté configurado para usar el lenguaje Python. n8n utiliza Pyodide (Python en WebAssembly) para esto.

### Código para el nodo "Code" (Python)

```python
from datetime import datetime

# En Python (Pyodide en n8n), accedemos a los items a través del array 'items'
# o usando el objeto global _input
return_items = []

for item in _input.all():
    # El payload del webhook
    body = item.json.get('body', item.json)
    
    # Analizamos el contenido de forma segura con .get()
    repo = body.get('repository', {})
    repo_name = repo.get('name', 'Desconocido')
    
    pusher = body.get('pusher', {})
    pusher_name = pusher.get('name', 'Desconocido')
    
    commits = body.get('commits', [])
    commits_count = len(commits)
    
    head_commit = body.get('head_commit', {})
    action_message = head_commit.get('message', 'Evento sin identificar')
    
    # Estructuramos los datos
    analyzed_data = {
        "source": "github_webhook",
        "event_type": "push",
        "repository": repo_name,
        "user": pusher_name,
        "total_commits": commits_count,
        "latest_commit_message": action_message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return_items.append({"json": analyzed_data})

return return_items
```

---

## El paso final: Enviar a Azure Event Hubs (HTTP Request)

Aunque podrías hacer la petición HTTP usando código (`fetch` en JS o `urllib/pyfetch` en Python), la **mejor práctica en n8n** es usar un nodo **HTTP Request** a continuación del nodo de Código. Esto maneja reintentos, timeouts y credenciales de forma mucho más robusta y segura.

### Configuración del nodo "HTTP Request":

Conecta la salida de tu nodo de Código a un nodo **HTTP Request** y configúralo de la siguiente manera:

- **Method:** `POST`
- **URL:** `https://<Tu-Namespace-EventHub>.servicebus.windows.net/<Tu-EventHub>/messages`
- **Authentication:** Dependiendo de Azure, suele ser a través de un **Header** o **Token (SAS)**. 
  - Puedes crear unas credenciales "Header Auth" en n8n pasando `Authorization` como nombre de la clave y tu Shared Access Signature (SAS) token como valor.
- **Send Headers:** Habilitado
  - Name: `Content-Type`
  - Value: `application/json`
- **Send Body:** Habilitado
- **Body Content Type:** `JSON`
- **Specify Body:** `Using Fields Below` o `JSON`. Si dejas que n8n use el JSON por defecto, enviará directamente el objeto `analyzedData` que creaste en el nodo de código.

### ¿Por qué separar el análisis del envío HTTP?
1. **Seguridad:** No quemas credenciales (Tokens SAS de Azure) directamente dentro de un script que podría subirse a un repositorio por error.
2. **Reintentos:** Si Azure Event Hub tiene un microcorte, el nodo HTTP de n8n permite configurar reintentos automáticos fácilmente sin programarlos a mano.
3. **Legibilidad:** Alguien que vea tu flujo visualmente sabrá exactamente qué está haciendo (Código -> Petición HTTP) sin tener que leer el script.
