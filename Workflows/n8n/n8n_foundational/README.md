# n8n: Automatización de Flujos de Trabajo (Low-Code)

n8n es una herramienta de automatización de flujos de trabajo de código abierto (o "fair-code") que permite conectar diferentes aplicaciones y servicios para automatizar tareas repetitivas sin necesidad de escribir mucho código (enfoque low-code).

## ¿Qué es n8n?

A diferencia de alternativas como Zapier o Make (antes Integromat), n8n ofrece:
- **Auto-alojamiento (Self-hosting):** Puedes ejecutarlo en tu propio servidor o localmente (como estamos haciendo con Docker), lo que te da control total sobre tus datos.
- **Nodos Extensibles:** Permite usar funciones de JavaScript para manipular datos complejos.
- **Estructura basada en nodos:** Los flujos se diseñan visualmente conectando "nodos" que representan acciones, disparadores (triggers) o lógica.

## Conceptos Clave

1. **Workflow (Flujo de Trabajo):** El conjunto de pasos que automatizan una tarea.
2. **Nodes (Nodos):** Los bloques de construcción. Hay nodos para aplicaciones (Slack, Google Sheets, GitHub), nodos de lógica (If, Merge) y nodos de datos (HTTP Request, Code).
3. **Triggers (Disparadores):** Nodos especiales que inician el flujo (por ejemplo, un webhook, un horario programado o un evento en una app).
4. **Credentials:** Configuración de seguridad para conectarse a servicios externos.

---

## Guía de Inicio Rápido

### 1. Levantar el servicio
Asegúrate de tener Docker instalado y ejecuta el siguiente comando en esta carpeta:

```bash
docker-compose up -d
```

### 2. Acceder a la interfaz
Una vez que el contenedor esté corriendo, abre tu navegador en:
[http://localhost:5678](http://localhost:5678)

### 3. Crear tu primer flujo
1. Crea una cuenta de usuario inicial (local).
2. Haz clic en "Add first step".
3. Busca el nodo **"On click"** (Manual Trigger) para probar manualmente.
4. Conecta un nodo de **"Code"** o **"HTTP Request"** para ver cómo fluyen los datos.

## Estructura de archivos
- `docker-compose.yml`: Configuración de Docker.
- `n8n_data/`: Carpeta persistente donde se guardan tus flujos, configuraciones y base de datos local (SQLite).