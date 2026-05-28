"""
Cliente SEGURO: pinning de host key.

Carga la clave publica esperada del servidor desde 'known_host.pub' (en
produccion vendria de un secreto, no de un fichero) y rechaza cualquier
otra. Si el atacante presenta una host key distinta, paramiko lanza
BadHostKeyException ANTES de mandar la contrasena.
"""

import sys
from pathlib import Path

import paramiko

HOST = "sokrates-vm"
USERNAME = "appuser"
PASSWORD = "s3cret-pharma-data"
REMOTE_FILE = "/data/secret.txt"
KNOWN_HOST_FILE = Path("/work/known_host.pub")  # montado desde el host


def main() -> int:
    if not KNOWN_HOST_FILE.exists():
        print(f"[secure] no encuentro {KNOWN_HOST_FILE}. "
              "Ejecuta primero el paso de captura de host key.", file=sys.stderr)
        return 2

    ssh = paramiko.SSHClient()

    # 1) Cargamos SOLO la host key que conocemos. No tocamos ~/.ssh/known_hosts
    #    para que el lab sea reproducible.
    ssh.get_host_keys().clear()
    ssh.load_host_keys(str(KNOWN_HOST_FILE))

    # 2) RejectPolicy: si la host key no esta en lo que cargamos arriba,
    #    falla. Sin trust-on-first-use, sin 'lo anado y sigo'.
    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

    print(f"[secure] conectando a {HOST} como {USERNAME} (politica = RejectPolicy)")
    try:
        ssh.connect(
            HOST,
            username=USERNAME,
            password=PASSWORD,
            timeout=10,
            allow_agent=False,
            look_for_keys=False,
        )
    except paramiko.BadHostKeyException as e:
        print(f"[secure] RECHAZADO: host key del servidor NO coincide. {e}")
        print("[secure] (la contrasena NO se ha enviado)")
        return 1
    except paramiko.SSHException as e:
        # 'Server <host> not found in known_hosts' cae aqui
        print(f"[secure] RECHAZADO ({type(e).__name__}): {e}")
        print("[secure] (la contrasena NO se ha enviado)")
        return 1

    print("[secure] conectado. Host key validada. Abriendo SFTP...")
    try:
        sftp = ssh.open_sftp()
        with sftp.open(REMOTE_FILE) as f:
            data = f.read().decode(errors="replace")
        print("[secure] LEIDO:", data)
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
