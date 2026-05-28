"""
Cliente VULNERABLE: reproduce literalmente el patron 'aceptar lo que sea'.

paramiko.AutoAddPolicy() significa: 'si no conozco la host key de este
servidor, dala por buena, anadela a known_hosts y sigue'. Eso elimina la
unica defensa contra MITM que tiene SSH cuando se usa contrasena:
verificar que la clave publica del servidor es la que esperabamos.

Si un atacante consigue que 'sokrates-vm' resuelva a su IP (DNS spoofing,
ARP spoofing, ruta envenenada, un proxy hostil...), AutoAddPolicy le
entrega la contrasena en bandeja: el cliente nunca avisa.
"""

import sys
import paramiko

HOST = "sokrates-vm"          # nombre logico; resuelve via extra_hosts
USERNAME = "appuser"
PASSWORD = "s3cret-pharma-data"
REMOTE_FILE = "/data/secret.txt"


def main() -> int:
    ssh = paramiko.SSHClient()
    # === LINEA PELIGROSA ===
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # =======================
    print(f"[vuln] conectando a {HOST} como {USERNAME} (politica = AutoAddPolicy)")
    ssh.connect(
        HOST,
        username=USERNAME,
        password=PASSWORD,
        timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )
    print("[vuln] conectado. Abriendo SFTP...")
    try:
        sftp = ssh.open_sftp()
        with sftp.open(REMOTE_FILE) as f:
            data = f.read().decode(errors="replace")
        print("[vuln] LEIDO:", data)
    except Exception as e:  # noqa: BLE001
        # Si estamos contra el atacante, el SFTP fallara; no importa,
        # la contrasena YA ha sido enviada y robada.
        print(f"[vuln] el SFTP fallo ({type(e).__name__}: {e}).")
        print("[vuln] OJO: la contrasena ya viajo al servidor.")
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
