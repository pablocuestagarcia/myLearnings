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

---

## Ejemplo Práctico: Recibir un Webhook de GitHub

Si quieres utilizar n8n para obtener datos que provienen de un evento en GitHub (por ejemplo, cuando alguien hace un *push*), puedes recibir esa petición HTTP y visualizar los datos siguiendo estos pasos:

### 1. Configurar el nodo en n8n
1. En tu Workflow, haz clic en **Add first step** y busca el nodo **Webhook**.
2. Configura el nodo:
   - **HTTP Method:** Selecciona `POST` (GitHub envía sus datos mediante POST).
   - **Path:** Ponle un nombre descriptivo, como `github-event`.
   - **Authentication:** Para pruebas, puedes dejarlo en `None`.
3. Haz clic en la pestaña **Test URL** dentro de la configuración del nodo y copia la URL que aparece.
   > ⚠️ **Importante si trabajas en local:** GitHub no puede enviar peticiones a `localhost`. Si estás ejecutando esto en tu PC local sin una IP pública, necesitarás usar una herramienta como [ngrok](https://ngrok.com/) (`ngrok http 5678`) para obtener una URL pública temporal que apunte a tu contenedor.

### 2. Poner a n8n a escuchar
En la ventana del nodo Webhook, haz clic en **"Listen for Test Event"**. n8n se quedará en estado de "escucha" esperando recibir la primera petición HTTP.

### 3. Configurar el Webhook en GitHub
1. Ve a tu repositorio en GitHub y entra en **Settings** > **Webhooks** > **Add webhook**.
2. En **Payload URL**, pega la URL que copiaste de n8n (o la de ngrok si estás en local).
3. En **Content type**, es muy importante seleccionar `application/json` para que n8n pueda procesar los datos estructurados automáticamente.
4. En la sección de eventos, puedes dejar "Just the push event" para probar.
5. Haz clic en **Add webhook**.

### 4. Visualizar los datos entrantes
En el mismo instante en que guardas el webhook en GitHub, la plataforma envía un evento de prueba (`ping`) a tu URL.
1. Vuelve a n8n. Verás que el nodo ha detectado la petición y ha terminado de ejecutarse ("Workflow executed successfully").
2. En el panel lateral derecho del nodo, bajo la pestaña **Output**, selecciona la vista **JSON**.
3. ¡Listo! Ahí podrás ver y navegar por todo el árbol de datos (`headers`, `body`, `query`) que GitHub te ha enviado. A partir de aquí, puedes conectar otros nodos a este webhook para procesar esos datos.