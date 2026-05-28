"""
Test automatizado del patron seguro, sin Docker.

Levanta un servidor SSH falso local (mismo truco que evil-server) con una
host key distinta de la pinada, y comprueba dos cosas:

  1. El cliente con AutoAddPolicy SI conecta y la 'password' acaba escrita
     en el log del servidor falso. Es decir: el ataque funciona.
  2. El cliente con RejectPolicy + host key pinada NO conecta y la password
     NUNCA aparece en el log. Es decir: el parche bloquea.

Este test es el que deberias ejecutar en CI para evitar que alguien revierta
el pinning por accidente. En produccion, copia este patron adaptandolo a tu
codigo real: importas TU funcion 'conectar()' (la parcheada) y compruebas
que lanza BadHostKeyException contra un servidor falso.

Ejecutar:
    pip install paramiko==3.4.0
    python tests/test_secure_client.py
"""

import io
import os
import socket
import sys
import tempfile
import threading
import time

import paramiko


# --- Servidor SSH falso (igual idea que evil-server, en proceso local) ---

class _EvilServer(paramiko.ServerInterface):
    def __init__(self, log_path: str) -> None:
        self.log_path = log_path

    def get_allowed_auths(self, username: str) -> str:
        return "password"

    def check_auth_password(self, username: str, password: str) -> int:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"user={username}|password={password}\n")
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


def _start_fake_server(host_key_path: str, log_path: str) -> int:
    """Arranca el servidor falso en un puerto libre y devuelve ese puerto."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.listen(5)

    def loop() -> None:
        while True:
            try:
                client_sock, _ = srv.accept()
            except OSError:
                return
            try:
                t = paramiko.Transport(client_sock)
                t.add_server_key(paramiko.RSAKey.from_private_key_file(host_key_path))
                t.start_server(server=_EvilServer(log_path))
                ch = t.accept(timeout=3)
                if ch is not None:
                    ch.close()
                t.close()
            except Exception:
                pass

    threading.Thread(target=loop, daemon=True).start()
    time.sleep(0.4)  # margen para que listen() este realmente activo
    return port


# --- Tests propiamente dichos ---

def test_attack_works_against_vulnerable_client(port: int, log_path: str) -> None:
    """Test 1: confirma que el escenario es real -- el atacante captura
    credenciales si el cliente usa AutoAddPolicy."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect("127.0.0.1", port=port, username="appuser",
                       password="s3cret-pharma-data", timeout=5,
                       allow_agent=False, look_for_keys=False)
    except Exception:
        pass
    finally:
        client.close()

    time.sleep(0.2)
    stolen = open(log_path).read()
    assert "user=appuser" in stolen and "password=s3cret-pharma-data" in stolen, \
        "Esperabamos ver las credenciales robadas en el log del servidor falso"
    print("  [OK] AutoAddPolicy + atacante -> credenciales en stolen.log")


def test_secure_client_blocks_attack(port: int, log_path: str) -> None:
    """Test 2: el cliente parcheado con host key pinada (a una clave distinta
    de la que presenta el servidor) debe lanzar BadHostKeyException
    ANTES de mandar la contrasena."""
    # Generamos UNA host key cualquiera distinta de la del servidor falso,
    # y la 'pinamos' como si fuera la del servidor legitimo. Simula que el
    # cliente conoce la host key real (esta) y el atacante presenta otra.
    pinned_key = paramiko.RSAKey.generate(2048)
    pinned_line = f"[127.0.0.1]:{port} ssh-rsa {pinned_key.get_base64()}\n"

    client = paramiko.SSHClient()
    client.get_host_keys().clear()
    # load_host_keys requiere un fichero; en produccion usariamos
    # io.StringIO + ssh.get_host_keys().load(...). Aqui usamos fichero
    # temporal solo porque load_host_keys exige path.
    with tempfile.NamedTemporaryFile("w", suffix=".pub", delete=False) as tmp:
        tmp.write(pinned_line)
        known_path = tmp.name
    try:
        client.load_host_keys(known_path)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

        before = open(log_path).read()
        raised = None
        try:
            client.connect("127.0.0.1", port=port, username="appuser",
                           password="s3cret-pharma-data", timeout=5,
                           allow_agent=False, look_for_keys=False)
        except paramiko.BadHostKeyException as e:
            raised = e
        finally:
            client.close()
        time.sleep(0.2)
        after = open(log_path).read()

        assert raised is not None, "Esperabamos BadHostKeyException y no salto"
        assert before == after, (
            "El log del servidor falso ha crecido -- el cliente seguro SI "
            "mando la password. Eso significa que el pinning no esta activo."
        )
        print("  [OK] RejectPolicy + pinning -> BadHostKeyException, password NO enviada")
    finally:
        os.unlink(known_path)


def main() -> int:
    tmpdir = tempfile.mkdtemp(prefix="paramiko-mitm-test-")
    host_key = os.path.join(tmpdir, "fake_host_key")
    paramiko.RSAKey.generate(2048).write_private_key_file(host_key)
    log_path = os.path.join(tmpdir, "stolen.log")
    open(log_path, "w").close()

    port = _start_fake_server(host_key, log_path)
    print(f"Servidor falso en 127.0.0.1:{port}, log en {log_path}")

    print()
    print("Test 1: el ataque funciona contra cliente vulnerable")
    test_attack_works_against_vulnerable_client(port, log_path)

    print()
    print("Test 2: el cliente seguro bloquea el ataque")
    test_secure_client_blocks_attack(port, log_path)

    print()
    print("Todos los tests pasaron. El patron de pinning funciona.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
