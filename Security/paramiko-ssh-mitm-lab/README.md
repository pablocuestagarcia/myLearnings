# Laboratorio: por qué `paramiko.AutoAddPolicy()` es inseguro

Lab reproducible con Docker Compose para *ver* — no leerlo en un blog, verlo en un log — cómo `paramiko.AutoAddPolicy()` deja a un cliente SSH indefenso ante un MITM, y cómo el *pinning* de host key lo bloquea.

El escenario simulado es un job Python que se conecta por SSH/SFTP a una VM remota (`sokrates-vm`) con usuario y contraseña para leer `/data/secret.txt`. El "ataque" se monta sin tocar la red: usamos `extra_hosts` en docker-compose para que dentro del contenedor cliente el nombre `sokrates-vm` resuelva al servidor del atacante en vez de al legítimo. A efectos de paramiko es exactamente lo mismo que un envenenamiento de DNS o ARP.

## ¿Esto es un runbook?

Sí, en sentido amplio. Un **runbook** es un documento operativo que dice *paso a paso* cómo ejecutar un procedimiento concreto: arrancarlo, comprobarlo, reaccionar si algo falla. Se distingue del manual de referencia (que describe *qué* hace el sistema) en que el runbook es accionable: "ejecuta esto, espera esto, si ves esto otro, haz aquello". Los SRE los usan para guardias y on-call; los equipos de plataforma para releases y migraciones; los de seguridad para responder a incidentes.

Este README es a la vez:

- **Runbook del lab** (la sección "Cómo levantarlo" más abajo describe la secuencia exacta y qué esperar en cada paso, que es lo que automatiza `scripts/run_demo.sh`).
- **Explicación didáctica** del fallo y su mitigación.

Para que se parezca aún más a un runbook "de verdad" he incluido los criterios de éxito de cada escenario (qué resultado se considera correcto). Un runbook real añadiría además sección de rollback y de troubleshooting; aquí no aplica porque levantar y tirar el lab es `docker compose up` / `docker compose down -v`.

## Estructura

```
paramiko-ssh-mitm-lab/
├── README.md                          (este fichero)
├── docker-compose.yml                 (servidores + servicio cliente)
├── docker-compose.client-legit.yml    (override: sokrates-vm -> legitimo)
├── docker-compose.client-evil.yml     (override: sokrates-vm -> atacante)
├── legit-server/Dockerfile            (sshd real con appuser y /data/secret.txt)
├── evil-server/Dockerfile             (servidor SSH falso basado en paramiko)
├── evil-server/evil_ssh_server.py     (acepta cualquier password y la loguea)
├── client/Dockerfile                  (python + paramiko + ssh-keyscan)
├── client/client_vulnerable.py        (usa AutoAddPolicy)
├── client/client_secure.py            (usa RejectPolicy + host key pinning)
├── tests/
│   └── test_secure_client.py          (test automatizable, sin Docker)
├── scripts/
│   ├── run_demo.sh                    (demo end-to-end en bash)
│   └── run_demo.ps1                   (demo end-to-end en PowerShell, para Windows)
└── HOTFIX.md                          (runbook operativo para aplicar el fix en prod)
```

## Requisitos

- Docker Desktop con Docker Compose v2 (`docker compose`, sin guion).
- Funciona en Windows (host del usuario), macOS y Linux. El backend WSL2 de Docker Desktop es perfectamente válido.
- Puertos: nada expuesto al host. Todo el tráfico vive dentro de la red Docker `lab-net` (172.28.0.0/24).

## Cómo levantarlo (runbook)

Desde la carpeta del lab:

**Windows (PowerShell):**

```powershell
.\scripts\run_demo.ps1
```

**Linux / macOS / WSL:**

```bash
bash scripts/run_demo.sh
```

El script ejecuta esta secuencia. Si prefieres hacerlo a mano para entender qué pasa:

1. Build y arranque de los dos servidores:
   ```
   docker compose build
   docker compose up -d legit-server evil-server
   ```
2. Capturar la host key del legítimo (la guardamos con el nombre `sokrates-vm`, que es el que el cliente usa):
   ```
   docker compose -f docker-compose.yml -f docker-compose.client-legit.yml run --rm client \
     bash -c 'ssh-keyscan -t ed25519 172.28.0.10 | sed "s|^172.28.0.10|sokrates-vm|" > /work/known_host.pub'
   ```
3. Escenario A — `client_vulnerable.py` contra el legítimo (override `client-legit`).
4. Escenario B — `client_vulnerable.py` contra el atacante (override `client-evil`). Después: `docker compose exec evil-server cat /var/log/stolen.log`.
5. Escenario C — `client_secure.py` contra el atacante.
6. Escenario D — `client_secure.py` contra el legítimo.

Para parar y limpiar: `docker compose down -v`.

## Qué se ve en cada escenario

**Escenario A — Legítimo + vulnerable.** El cliente vulnerable conecta al servidor real, AutoAddPolicy acepta la host key (no la conocía), se autentica con la contraseña y lee `datos confidenciales del pharma pipeline`. *Aparentemente* todo funciona. Este es el caso que en producción se pasa por bueno años. El problema es que está pasando por bueno también el modo MITM, sin que nadie se entere.

**Escenario B — Atacante + vulnerable. El ataque.** El cliente cree que se está conectando a `sokrates-vm` (que en su `/etc/hosts` apunta a 172.28.0.20). AutoAddPolicy acepta la host key *distinta* que presenta el atacante sin avisar, el cliente envía la contraseña en claro al canal cifrado, y `evil_ssh_server.py` la registra en `/var/log/stolen.log`. Cuando hacemos `cat` de ese log vemos la línea con `user='appuser' password='s3cret-pharma-data'`. Este es el momento didáctico clave: **la única defensa contra MITM con auth por contraseña es verificar la host key, y AutoAddPolicy la desactiva**.

**Escenario C — Atacante + seguro.** Mismo apuntamiento al atacante, pero el cliente carga `known_host.pub` (la clave del legítimo, capturada en el paso 1) y usa `RejectPolicy`. Paramiko ve que la host key que presenta `172.28.0.20` no coincide con la esperada para `sokrates-vm`, lanza `BadHostKeyException` y aborta **antes** de la fase de autenticación. El script comprueba `wc -l` de `stolen.log` antes y después: el contador no cambia. La contraseña no ha viajado.

**Escenario D — Legítimo + seguro.** El cliente seguro conecta al legítimo, valida la host key contra `known_host.pub`, se autentica y lee el fichero. Demuestra que la versión segura no rompe el flujo bueno; solo bloquea el malo.

## Cómo se traduce esto a producción

El cliente seguro de este lab carga la host key esperada desde un fichero `known_host.pub` montado en el contenedor. En un job Python real eso es una mala idea: el fichero acabaría en el repo, o en un volumen al que la gente equivocada tiene acceso. El patrón correcto es **guardar la host key del servidor como secreto en un secret manager** (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, Google Secret Manager, variables de entorno inyectadas por el orquestador desde uno de ellos, etc.) y cargarla en memoria antes de conectar. Equivalente al `load_host_keys(path)` del lab pero leyendo el secreto:

```python
import io
import paramiko

# 'secret' es la cadena 'sokrates-vm ssh-ed25519 AAAA...' tal cual la
# devolveria 'ssh-keyscan' (rotada/pinada en el secret store)
secret = obtener_secreto("sokrates_vm_host_key")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
ssh.get_host_keys().load(io.StringIO(secret))
ssh.connect("sokrates-vm", username="appuser", password=obtener_secreto("sokrates_vm_password"))
```

Tres ideas clave para llevarse:

1. **Nunca** `AutoAddPolicy()` en código que no sea un script puntual interactivo donde una persona pueda comparar el fingerprint a mano. En un job no atendido, equivale a desactivar la verificación.
2. La host key esperada es un dato igual de sensible que la propia contraseña: trátalo como secreto, rotación incluida cuando se reinstale la VM remota.
3. Si puedes, pasa de auth por contraseña a auth por clave pública (claves del cliente generadas en el secret manager y rotadas) — aun así, el pinning de host key sigue siendo necesario para evitar MITM, no se sustituyen entre sí.

## Glosario rápido

**Host key.** Par de claves (privada + pública) que `sshd` genera la primera vez que se instala. La pública se manda al cliente en cada handshake como prueba de identidad del servidor. Distinta de las claves de *usuario* que se usan en auth por clave pública: aquí hablamos de la identidad del *servidor*, no de la del cliente.

**Pinning de host key.** Decir explícitamente "para este host, la host key esperada es ésta y solo ésta". Lo opuesto a "acepto la que me presenten". Es el control que un cliente con auth por contraseña tiene para defenderse de un MITM.

**TOFU (Trust On First Use).** Modelo de confianza en el que se acepta como buena la identidad presentada en la *primera* conexión y se persiste; las conexiones siguientes se validan contra esa primera. Cero configuración previa, pero si esa primera conexión ya estaba interceptada, confías en el atacante para siempre. SSH manual con prompt es TOFU con humano. `AutoAddPolicy()` es TOFU sin prompt — peor, porque quita al humano. `ssh-keyscan` también es TOFU si lo lanzas desde un sitio que podría estar comprometido.

**MITM (Man-In-The-Middle).** Atacante que se mete entre cliente y servidor, suplantando a uno ante el otro. Para SSH con password auth, la única defensa real del cliente es comprobar que la host key del servidor es la esperada — porque si no, está mandando la contraseña por un canal cifrado, sí, pero cifrado *con el atacante*.

## Si estás aplicando esto como hotfix en producción

Si llegaste a este lab buscando cómo arreglar un `AutoAddPolicy()` en código real **sin** poder tocar el servidor remoto y **manteniendo** auth por usuario/contraseña, lee [HOTFIX.md](HOTFIX.md). Es el runbook operativo paso a paso: cómo capturar la host key del servidor existente de forma fiable, dónde guardarla, el parche exacto en el cliente Python, cómo verificar antes de desplegar, y plan de mejora para después.

## Troubleshooting de build

**Si el `docker compose build` falla con `Error reading from server. Remote end closed connection [IP: 151.101.…]` o `404 Not Found` en `deb.debian.org`:** es el CDN de Debian (Fastly) cortando descargas. Los Dockerfiles ya tienen 10 reintentos y timeout de 60s, así que normalmente basta con relanzar el build:

```
docker compose build --no-cache legit-server
```

Si persiste, hay alternativas Alpine listas — `legit-server/Dockerfile.alpine` y `client/Dockerfile.alpine`. Para activarlas, en `docker-compose.yml` cambia los bloques `build` así:

```yaml
  legit-server:
    build:
      context: ./legit-server
      dockerfile: Dockerfile.alpine
  client:
    build:
      context: ./client
      dockerfile: Dockerfile.alpine
```

y vuelve a lanzar `docker compose build`. Alpine usa otro CDN (`dl-cdn.alpinelinux.org`) y los paquetes son mucho más pequeños, así que un blip de red ya no rompe el build entero.

## Limpieza

```
docker compose down -v
rm -f known_host.pub
```

`-v` elimina los volúmenes anónimos; las host keys generadas en build se reconstruyen la próxima vez que hagas `build`.
