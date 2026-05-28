# Hotfix: parchear `paramiko.AutoAddPolicy()` sin tocar el servidor ni cambiar el método de autenticación

Documento operativo. Pensado para cuando ya tienes en producción un job Python que se conecta por SSH/SFTP a una VM remota con usuario y contraseña, descubres que usa `paramiko.AutoAddPolicy()`, y necesitas mitigarlo *ya* — sin migrar a auth por clave pública, sin redesplegar la VM, sin coordinar con el equipo que mantiene el servidor más allá de lo imprescindible.

Si no has leído el [README.md](README.md), hazlo primero: explica el lab y por qué `AutoAddPolicy` es inseguro. Este documento asume que ya entiendes el problema y se centra en el procedimiento de parcheo.

## Antes de empezar: vocabulario operativo

Para no asumir conocimiento que no se tenga al primer empleo, los términos exactos que vas a leer aquí, todos definidos para que el documento se lea solo:

- **Host key.** Par de claves (privada + pública) que genera `sshd` (el daemon SSH) la primera vez que se instala en un servidor. Vive en `/etc/ssh/`, típicamente como `ssh_host_ed25519_key` (privada) y `ssh_host_ed25519_key.pub` (pública). La pública se manda al cliente en cada handshake como prueba de identidad. **No es** la clave del usuario para auth pubkey: es la identidad *del servidor*.
- **Pinning de host key.** Decir explícitamente en el cliente "para este host, la host key esperada es ésta". Lo opuesto a aceptar la que se presente.
- **Fingerprint.** Hash corto (SHA-256 hoy en día) de una clave pública. Sirve para que un humano lea por teléfono o vea por pantalla algo manejable en vez de cientos de caracteres en base64.
- **Fuera de banda (out-of-band).** Usar un canal de comunicación *distinto* del que estás intentando validar. Ejemplo: si dudas de si tu conexión SSH a una VM está siendo interceptada, validar por SSH no sirve; tienes que mirar la VM por otro canal (consola web del cloud provider, llamada al sysadmin, ticket en Jira). Out-of-band = "por otra vía".
- **TOFU (Trust On First Use).** Confiar a ciegas la primera vez que ves una identidad, y persistirla. Cero configuración previa, pero si esa primera vez ya estabas interceptado, has fijado al atacante. SSH manual con prompt "do you want to continue connecting?" es TOFU con humano.
- **MITM (Man-In-The-Middle).** Atacante interpuesto entre cliente y servidor, suplantando a cada uno ante el otro. Contra auth por contraseña, la única defensa práctica del cliente es validar la host key del servidor.
- **Secret manager.** Servicio donde guardas datos sensibles (contraseñas, tokens, claves) en lugar de meterlos en código o variables de entorno hardcoded. Ejemplos: Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, Google Secret Manager. Si no tienes uno, lo mínimo aceptable es una variable de entorno inyectada por tu orquestador (Kubernetes Secret, GitHub Actions secret) — el código no debe contener el valor.
- **Rotación.** Sustituir un secreto por uno nuevo de forma controlada (porque caducó, porque sospechas que se ha filtrado, porque la infraestructura cambió). Aplica tanto a contraseñas como a host keys: si el equipo de infra reinstala el servidor, su host key cambiará y hay que actualizar el secreto en el cliente.

## Camino mínimo deployable hoy

Si solo necesitas desplegar el fix lo antes posible y luego iterar a la versión recomendada, este es el procedimiento más corto posible. Asume que no tienes acceso fuera de banda al servidor y que no quieres molestar a nadie del equipo de infra. Es la opción (d) del Paso 1 + Paso 2 + Paso 3 destilados:

**1) Capturar la host key del servidor desde tu máquina.** Tienes dos sub-opciones, prefiere la primera si aplica:

**1a — Atajo si ya SSHeas habitualmente a esa máquina con `ssh` (no paramiko).** Tu `~/.ssh/known_hosts` ya tiene la entrada desde tu primera conexión, y OpenSSH la lleva validando en cada conexión posterior. Si nunca te ha saltado un `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`, esa entrada es la real. Sácala directamente del fichero:

```
grep sokrates-vm ~/.ssh/known_hosts
```

Una sola línea, ya en formato `known_hosts`, lista para subir al secret manager. Esta vía no introduce TOFU nuevo — reutiliza la confianza acumulada por tu uso habitual durante meses.

**1b — Si no tienes la entrada previa**, `ssh-keyscan` desde una máquina de confianza (portátil corporativo administrado), idealmente en momento de poca actividad:

```
ssh-keyscan -t ed25519 sokrates-vm > sokrates_host_key.txt
```

Abre el fichero y comprueba que tiene una sola línea con el formato `sokrates-vm ssh-ed25519 AAAA...`. Si la primera columna es una IP en vez del hostname, edítalo a mano para que ponga `sokrates-vm` (el mismo nombre que use tu `ssh.connect(...)`).

**Advertencia honesta sobre 1b:** esto es TOFU — confías en que tu red no esté MITM-eada en ese instante. Si quieres elevar la confianza, lanza `ssh-keyscan -t ed25519 sokrates-vm | ssh-keygen -lf -` desde varias máquinas independientes (otra red, runner de CI) y compara que el fingerprint coincide en todas. Un MITM tendría que estar activo en todas las rutas a la vez para falsearlo. En cualquier caso, es **dramáticamente** mejor que dejar `AutoAddPolicy()`: ese TOFU pasa una sola vez en un instante que tú controlas, en lugar de en cada conexión durante meses sin que nadie se entere.

**Por qué SSHear al servidor y leer `/etc/ssh/ssh_host_*.pub` no es más seguro que `ssh-keyscan`.** Tentación común: "tengo las credenciales, entro al servidor, copio el fichero". El problema es que esa sesión SSH viaja por la misma red, contra el mismo hostname, en el mismo instante que cualquier conexión del pipeline. Si hay MITM, te lleva al atacante, que puede mostrarte la host key que él quiera al hacer `cat`. La sesión SSH valida lo mismo que necesitas validar — es circular. Esta vía solo es más segura que `ssh-keyscan` **si la haces desde una máquina cuyo `known_hosts` ya tiene la entrada validada** (caso 1a). Si no, son equivalentes.

**2) Subir el contenido del fichero a tu secret manager**, con un nombre tipo `sokrates_vm_host_key` (paralelo al `sokrates_vm_password` que ya tendrás). Una sola entrada, valor = la línea entera del fichero. Luego borra el fichero local; ya no lo necesitas.

**3) Aplicar este parche en tu código** (las líneas marcadas con `# +` son las nuevas; el resto ya estaba):

```python
import io                                                          # +
import paramiko

ssh = paramiko.SSHClient()
ssh.get_host_keys().clear()                                        # +
ssh.get_host_keys().load(io.StringIO(                              # +
    get_secret("sokrates_vm_host_key")))                           # +
ssh.set_missing_host_key_policy(paramiko.RejectPolicy())           # cambia AutoAddPolicy() por esto
ssh.connect("sokrates-vm",
            username="appuser",
            password=get_secret("sokrates_vm_password"),
            timeout=10,
            allow_agent=False, look_for_keys=False)                # + (recomendado)
```

Despliega. Si el job conecta y lee el fichero, has terminado el hotfix. Si lanza `BadHostKeyException` contra el servidor legítimo, la captura del paso 1 fue mala — vuelve a capturar y rota el secreto.

**Qué queda pendiente tras este camino corto** (revisar antes de cerrar el ticket del hotfix, no después):

- El paso 1 es TOFU. Cuando puedas, sustitúyelo por la opción (a), (b) o (c) del Paso 1 completo (más abajo). El parche del cliente **no cambia**, solo cambia cómo capturas la host key que metes en el secret manager.
- No tienes proceso de rotación. Si mañana el equipo de infra reinstala la VM, tu job se cae. Ver "Plan de mejora post-hotfix" al final.
- La password sigue viajando por la sesión SSH. El siguiente proyecto debería ser migrar a auth por clave pública.

Si necesitas más contexto sobre **por qué** cada cosa es como es, o quieres una opción del paso 1 más robusta que TOFU, sigue leyendo. Si solo querías la versión deployable, has terminado.

## TL;DR

- **No hace falta tocar el servidor remoto.** El servidor ya tiene una host key (la generó `sshd` solo al instalarse). Tú solo necesitas conocerla.
- **No hace falta cambiar el método de autenticación.** Sigues mandando `username` + `password`. La diferencia es que paramiko ahora verifica la identidad del servidor antes de autenticar, y aborta si no coincide con lo esperado.
- **El cambio en código son tres líneas.** Limpiar la lista de hosts conocidos que paramiko cargaría por defecto, cargar la host key esperada desde el secret manager, y cambiar la política de `AutoAddPolicy` a `RejectPolicy`.
- **El trabajo de verdad está en capturar la host key del servidor real una sola vez, desde un canal en el que confíes.** Si capturas mal (con un atacante en medio en ese instante), acabas pinando la identidad del atacante como si fuera la del servidor real. Si capturas bien, has eliminado el agujero.

## Lo que NO necesitas tocar

- El `sshd_config` del servidor remoto.
- Los usuarios, contraseñas o permisos en el servidor.
- Las claves del servidor (no regenerar, no rotar como parte del hotfix).
- El método de autenticación del cliente (sigues con password).

Lo único que sí tienes que tocar:

- El código Python del cliente (3 líneas, sección "Paso 3").
- El secret manager donde guardas la contraseña — añades una entrada nueva: la host key del servidor.

## Paso 1: capturar la host key del servidor real, de forma fiable

Este es **el paso crítico**. Capturar mal la host key tiene el mismo problema que TOFU: si en el momento de capturarla había un MITM, acabas pinando la identidad del atacante como si fuera la del servidor real. Las opciones, ordenadas por fiabilidad (de más fiable a "lo mínimo aceptable"):

### (a) Acceso fuera de banda al servidor — ideal

Aquí "fuera de banda" significa: entrar a la VM por un canal que **no** sea el SSH que estás intentando validar. Si la respuesta llega por la misma red que dudas, no estás validando nada. Las opciones más comunes según tu cloud:

- **Consola serie del cloud provider.** Una sesión de consola tipo terminal que el cloud provider te abre directamente en la VM por su propia infraestructura, sin pasar por la red pública de la VM. Azure la llama "Serial console", AWS "EC2 Serial Console", GCP "Serial console". Disponible desde el portal web tras autenticarte como administrador del cloud.
- **Bastion / jump host.** Una máquina pequeña y muy controlada en la misma red privada que la VM, a la que tú accedes (por SSH también, sí, pero a *otra* IP y otra clave). Desde el bastion, la VM se ve por su IP interna.
- **Servicios "run command" sin SSH.** Azure VM Run Command, AWS SSM Session Manager, GCP `gcloud compute ssh --tunnel-through-iap`. Permiten ejecutar comandos en la VM sin abrir SSH desde fuera; usan canales del cloud provider autenticados con tus credenciales del cloud.

Una vez dentro por uno de esos canales, vuelcas las claves públicas tal cual están en disco:

```
cat /etc/ssh/ssh_host_ed25519_key.pub
cat /etc/ssh/ssh_host_rsa_key.pub
```

Lo que copies de ahí es definitivamente la host key real, porque esa lectura no ha pasado por la red SSH que estás intentando validar. Esta es la opción correcta si tu plataforma te la permite.

### (b) Pedir el fingerprint al sysadmin y cruzar contra `ssh-keyscan`

Si no puedes meterte tú, pídele al equipo que mantiene la VM que ejecute en la VM:

```
for f in /etc/ssh/ssh_host_*_key.pub; do ssh-keygen -lf "$f"; done
```

Esto te devuelve fingerprints con este aspecto:

```
256 SHA256:abcdEFGHijkl...mnop root@sokrates-vm (ED25519)
3072 SHA256:wxyzABCDefgh...rstu root@sokrates-vm (RSA)
```

Lectura del fingerprint: `256` o `3072` es el tamaño de la clave en bits, `SHA256:...` es el hash de la clave pública (esto es lo que tienes que comparar), `root@sokrates-vm` es solo un comentario que `ssh-keygen` mete en el `.pub` cuando se generó (no aporta seguridad, ignóralo) y entre paréntesis va el tipo de clave.

El sysadmin te lo pasa por un canal donde ya autenticas a esa persona por otros medios (correo corporativo de su cuenta + verificación rápida por chat, ticket de Jira asignado a una persona que conoces, llamada). La idea es que confías en el canal porque ya hay una autenticación previa (login corporativo, número de teléfono conocido).

Luego tú, desde tu red de producción, lanzas el equivalente con `ssh-keyscan` para que te muestre el fingerprint visto por la red:

```
ssh-keyscan -t ed25519 sokrates-vm | ssh-keygen -lf -
```

El `-` final significa "lee desde stdin" — es decir, le pasas la salida de `ssh-keyscan` directamente a `ssh-keygen` por pipe.

Si los dos fingerprints (el del sysadmin y el de `ssh-keyscan` por red) coinciden, validado: la captura por red es la real. Si **no** coinciden, hay alguien en medio de tu red *ahora mismo* interceptando el tráfico hacia esa IP — esto deja de ser un hotfix tuyo y pasa a ser un incidente de seguridad (avisa a quien corresponda en tu organización antes de seguir).

### (c) Cross-check con tu infraestructura como código

Si la VM se provisionó con Terraform o Ansible, la host key puede estar capturada en algún sitio que ya controlas. Para que esto te sirva, necesitas alguna de estas dos cosas:

- **Terraform output:** algunos módulos de Terraform que crean VMs exponen el fingerprint o la host key del SSH como atributo del recurso. Si tu módulo lo hace, está en `terraform.tfstate` o en una variable de salida documentada.
- **Ansible fact:** cuando Ansible se conecta a una VM por primera vez, recoge variables sobre la máquina ("facts"). Entre ellas, `ansible_ssh_host_key_ed25519_public`. Si tienes un playbook que ya se conectó alguna vez, esos facts pueden estar cacheados.

Si tienes uno de los dos, compara ese valor histórico con lo que devuelve `ssh-keyscan` ahora. Mismo principio que (b), pero la fuente fiable es tu propia infraestructura como código en vez de un sysadmin humano.

### (d) `ssh-keyscan` sin nada que cruzar — mínimo viable

Si no tienes ninguna de las opciones anteriores (sin acceso fuera de banda, sin sysadmin disponible, sin infraestructura como código con la key), te queda lanzar `ssh-keyscan` desde tu red y aceptar lo que devuelva. Esto **es TOFU**: confías en que tu red no esté MITM-eada *en este preciso instante* y fijas para siempre lo que veas.

No es ideal, pero es **dramáticamente mejor que dejar `AutoAddPolicy()`**: AutoAddPolicy acepta lo que sea cada vez que el cliente conecta, durante meses o años; esto solo confía en la red una vez, en un instante que tú eliges y controlas. Recomendaciones para que ese único momento sea lo más fiable posible:

- Hazlo en una ventana de mantenimiento, cuando hay menos actividad en la red.
- Desde una máquina recién parcheada y de la que estás seguro (un portátil corporativo administrado, no un equipo personal cualquiera).
- Si tu organización tiene VPN, decide a conciencia si conviene tenerla activa o no: con la VPN activa, el tráfico va por la red corporativa (más controlada normalmente, pero si está comprometida lo está en bloque); sin VPN, va por tu red local + internet (más expuesta a ataques de red local, pero independiente de la corporativa). Si la VM está en una red privada del cloud y solo es alcanzable vía VPN, no tienes elección.

### Formato final de la host key

Sea cual sea la opción que uses, el resultado debe quedar como una línea con tres campos separados por espacios, exactamente el formato del fichero `~/.ssh/known_hosts`:

```
sokrates-vm ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxx
```

Los tres campos son: nombre del host (el que use tu cliente al llamar a `connect()`), tipo de clave, clave pública en base64. Si capturaste con `ssh-keyscan -t ed25519 172.x.x.x`, la primera columna te saldrá con la IP; reescríbela al hostname lógico (`sokrates-vm` o el que sea) para que paramiko lo case con el `connect("sokrates-vm", …)` del código.

## Paso 2: guardar la host key como secreto

La host key es tan sensible como la contraseña, por la misma razón: quien la conoce puede suplantar al servidor ante un cliente que la valida. **No la pongas en el repo**, no la pongas en variables de entorno hardcoded en el Dockerfile, no la pongas en un fichero junto al código.

Súbela a tu secret manager (el mismo que ya uses para la contraseña). Sugerencia de nombre: `sokrates_vm_host_key`, paralelo al `sokrates_vm_password` que ya tendrás. El valor es la línea entera del paso 1, tal cual.

Marca la versión actual del secreto como `v1` o con la fecha de captura. Esto te servirá cuando haya que rotar — por ejemplo, si el equipo de infra reinstala la VM (la host key se regenera) o sospechas que se ha filtrado: en ambos casos generas una `v2` con la nueva clave, actualizas el cliente para que lea `v2`, y dejas `v1` archivada un tiempo por si necesitas rollback.

## Paso 3: el parche en el código Python

### Antes (vulnerable)

```python
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("sokrates-vm", username="appuser",
            password=get_secret("sokrates_vm_password"),
            timeout=10)
sftp = ssh.open_sftp()
with sftp.open("/data/secret.txt") as f:
    data = f.read()
ssh.close()
```

### Después (parcheado, conservando password auth)

```python
import io
import paramiko

ssh = paramiko.SSHClient()

# (1) Vaciar la lista de hosts conocidos.
#     SSHClient() arranca con la lista vacia, pero si en algun sitio del
#     codigo se llamaba a load_system_host_keys() o load_host_keys(...),
#     habria entradas de ~/.ssh/known_hosts o /etc/ssh/ssh_known_hosts.
#     Esas entradas no nos las hemos validado nosotros: las limpiamos
#     para que la unica fuente de verdad sea la del paso (2).
ssh.get_host_keys().clear()

# (2) Cargar la host key esperada DESDE EL SECRET MANAGER.
#     load() espera un objeto tipo fichero, no una cadena. Como la
#     cadena la tenemos en memoria (viene de get_secret), la envolvemos
#     con io.StringIO, que da un interfaz de fichero sobre una cadena.
ssh.get_host_keys().load(io.StringIO(get_secret("sokrates_vm_host_key")))

# (3) Si paramiko se topa con un host que no esta en la lista pinada,
#     que ABORTE. Nada de "lo anado y sigo" (AutoAddPolicy), nada de
#     "aviso y sigo" (WarningPolicy).
ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

ssh.connect(
    "sokrates-vm",
    username="appuser",
    password=get_secret("sokrates_vm_password"),
    timeout=10,
    # (4) Bloquear que paramiko use credenciales del entorno:
    #     - allow_agent=False: no preguntar al ssh-agent (un servicio
    #       que el SO mantiene con claves SSH del usuario cacheadas).
    #     - look_for_keys=False: no leer ~/.ssh/id_rsa, id_ed25519, etc.
    #     En un job no atendido nunca quieres estas vias, y dejarlas
    #     abiertas puede enmascarar fallos del flujo previsto.
    allow_agent=False,
    look_for_keys=False,
)
sftp = ssh.open_sftp()
with sftp.open("/data/secret.txt") as f:
    data = f.read()
ssh.close()
```

Diferencias entre los dos bloques: tres líneas nuevas antes del `connect` (puntos 1, 2, 3), cambio de `AutoAddPolicy` a `RejectPolicy`, y los dos kwargs nuevos en el `connect` (punto 4). Nada más cambia.

### Qué es `get_secret` y cómo implementarla

`get_secret` no existe en paramiko, es una función que tienes que escribir tú (o que tu equipo ya tiene en alguna librería interna). Su trabajo es ir al secret manager, pedir el valor por nombre, y devolverlo como cadena. Dos ejemplos concretos según dónde tengas los secretos:

**Variable de entorno (lo mínimo aceptable, p.ej. Kubernetes Secret montado como env vars):**

```python
import os

def get_secret(name: str) -> str:
    # Convencion: nombres en MAYUSCULAS, prefijo del servicio
    env_var = name.upper()  # 'sokrates_vm_password' -> 'SOKRATES_VM_PASSWORD'
    value = os.environ.get(env_var)
    if value is None:
        raise RuntimeError(f"Secret '{name}' no esta en env como {env_var}")
    return value
```

**Azure Key Vault (típico de un job Python desplegado en Azure):**

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

_VAULT_URL = "https://mi-keyvault.vault.azure.net"
_client = SecretClient(vault_url=_VAULT_URL, credential=DefaultAzureCredential())

def get_secret(name: str) -> str:
    # Key Vault no acepta guiones bajos en los nombres; convertimos
    # 'sokrates_vm_password' -> 'sokrates-vm-password'
    kv_name = name.replace("_", "-")
    return _client.get_secret(kv_name).value
```

Cualquier otro secret manager (AWS Secrets Manager, HashiCorp Vault, Google Secret Manager) tiene un SDK Python equivalente: el patrón es el mismo, solo cambia el cliente.

## Paso 4: verificación antes de desplegar

No despliegues sin probarlo. Tres comprobaciones en orden, de más rápida a más realista:

### 4.1 Test local contra el lab

Este repo es exactamente eso. Lanza `scripts/run_demo.sh` (o `.ps1` en Windows). El escenario C — MITM + cliente seguro — reproduce el patrón que vas a desplegar. Si en tu copia local no ves `BadHostKeyException` y la línea "Password NO enviada", algo está mal en tu pinning *antes* de tocar producción.

### 4.2 Test unitario con servidor falso (incluido en este repo)

`tests/test_secure_client.py` arranca un servidor SSH falso local (mismo patrón que `evil-server` pero en proceso), presenta una host key distinta de la pinada, y comprueba dos cosas:

1. Que el atacante captura credenciales si el cliente usa `AutoAddPolicy` — confirma que el escenario de ataque es real.
2. Que el cliente con `RejectPolicy` + host key pinada lanza `BadHostKeyException` y **no** escribe nada en el log del servidor falso — confirma que el pinning bloquea.

```
pip install paramiko==3.4.0
python tests/test_secure_client.py
```

Adapta este test a tu repo real: importa tu función `conectar()` (la parcheada), arranca el servidor falso, y haz `assert raises(BadHostKeyException)`. Mételo en CI. Si alguien revierte el pinning en un PR futuro, este test falla y nadie lo merguea.

### 4.3 Smoke test contra el servidor real, en staging

Despliega la versión parcheada en un entorno equivalente con un secret apuntando a una host key correcta. Una conexión debe funcionar. Luego cambia el secret a una host key ficticia (puedes generar una con `ssh-keygen -t ed25519 -f /tmp/fake -N ''` y usar `/tmp/fake.pub`) y vuelve a conectar — debe romperse con `BadHostKeyException`, no con timeout, no con "authentication failed". Eso te confirma que paramiko está validando antes de autenticar.

## Paso 5: despliegue y rollback

Recomendaciones operativas:

- **Despliega en horario laboral** del equipo que mantiene la VM remota. Si capturaste mal la host key, el job va a empezar a fallar; necesitas estar disponible para corregir el secret rápido.
- **Logging.** Asegúrate de que la excepción `BadHostKeyException` se loguea con detalle. Por defecto su mensaje tiene este aspecto:

  ```
  paramiko.ssh_exception.BadHostKeyException: Host key for server 'sokrates-vm' does not match: got 'AAAAB3NzaC1yc2EAAAAD...', expected 'AAAAC3NzaC1lZDI1NTE5AAAAI...'
  ```

  Es decir, te dice qué host key recibió y qué esperaba. Capturar `got` vs `expected` en el log te ayudará a diagnosticar rápido si el problema es que has capturado mal la host key (corriges el secret), o si el servidor de verdad rotó su host key sin que te avisaran (mismo arreglo: nueva captura, nuevo secret).
- **Rollback.** Volver a la versión anterior del job (la del `AutoAddPolicy`) es rollback válido si el hotfix está rompiendo producción y no encuentras la causa rápido. Es feo (vuelves al estado vulnerable), pero es lo correcto si la alternativa es un job parado horas. Documenta el rollback como incidente y vuelve a abordarlo con calma.

## Lo que sigue sin estar arreglado tras el hotfix

Este hotfix te saca del peor escenario (`AutoAddPolicy`, vulnerable a cualquier MITM oportunista) y te deja en uno mucho mejor (host key pinada). Pero:

1. **La contraseña sigue viajando por la sesión SSH.** Cifrada, sí, pero presente. Si el servidor legítimo se compromete (un atacante con shell en la VM puede leer lo que reciba `sshd`), la contraseña queda expuesta. La defensa contra esto es auth por clave pública, no contraseña.
2. **Si la VM rota su host key (reinstalación, regeneración manual, cambio de imagen), tu job dejará de funcionar.** No tenías ese riesgo con `AutoAddPolicy` porque aceptaba lo que fuera; lo tienes ahora porque rechaza lo que no coincida. Necesitas proceso: que el equipo que mantiene la VM avise antes de tocar host keys, y que rotes el secreto en paralelo.
3. **El paso 1 sigue siendo TOFU si no llegaste a la opción (a).** Hasta que la host key venga del provisioner o de un canal completamente fuera de banda, hay una ventana en la que confías en la red.

## Plan de mejora post-hotfix

Por orden de impacto/coste:

- **Proceso de rotación de host key.** Un runbook corto, asignado a alguien. Cuando el equipo de infra reinstale o regenere, abren ticket, ejecutan paso 1 con la nueva clave, actualizan el secreto, despliegan. Sin esto, el hotfix tiene fecha de caducidad invisible.
- **Migración a auth por clave pública** (no es hotfix, es proyecto). Generas keypair, la pública va al `authorized_keys` del `appuser` en la VM, la privada al secret manager, quitas el password del código. Elimina el riesgo (1) de arriba.
- **Host key desde el provisioner** para VMs nuevas. Si Terraform crea la VM, que el output del módulo incluya la host key. Elimina el riesgo (3) de arriba.

## Anti-patrones que parecen seguros pero no lo son

- **`paramiko.WarningPolicy()`**. Cuando ve una host key desconocida, escribe un warning en logs y *conecta igual*. No es defensa, es un log más que nadie lee.
- **`load_system_host_keys()` solo**, sin pinning explícito desde un secreto. Lee `~/.ssh/known_hosts` del usuario que ejecuta el proceso. En un contenedor recién creado ese fichero suele estar vacío → vuelves a TOFU implícito en la primera conexión.
- **Capturar la host key con `ssh-keyscan` *dentro* del propio job, en cada arranque**, y guardarla en un volumen para validarla las siguientes veces. Estás haciendo TOFU manual cada vez que el contenedor es nuevo. Equivalente a `AutoAddPolicy` con pasos extra.
- **Pinar el fingerprint en vez de la clave pública entera.** Técnicamente válido (el fingerprint es SHA-256 de la clave; si coincide, la clave coincide), pero paramiko no tiene política built-in para esto: necesitas escribirte una subclase de `paramiko.MissingHostKeyPolicy` que calcule el hash de la clave recibida y lo compare con tu fingerprint guardado. Es más código y más sitio donde meter la pata. Pinear la línea entera de `known_hosts` y dejar que `RejectPolicy` haga su trabajo es estándar y más seguro frente a bugs propios.
