#!/usr/bin/env bash
# Demo end-to-end del lab paramiko AutoAddPolicy MITM.
# Pensado para ejecutarse desde la raiz del lab o desde scripts/.

set -uo pipefail
cd "$(dirname "$0")/.."

COMPOSE_BASE=(-f docker-compose.yml)
LEGIT=(-f docker-compose.client-legit.yml)
EVIL=(-f docker-compose.client-evil.yml)

separator() {
  echo
  echo "============================================================"
  echo "$@"
  echo "============================================================"
}

separator "Paso 0: build + arranque de los dos servidores"
docker compose "${COMPOSE_BASE[@]}" build
docker compose "${COMPOSE_BASE[@]}" up -d legit-server evil-server
echo "Esperando 6s a que sshd este escuchando..."
sleep 6

separator "Paso 1: capturar host key del LEGITIMO (172.28.0.10) y guardarla como sokrates-vm"
# Reescribimos la primera columna (IP) al hostname que usara el cliente.
docker compose "${COMPOSE_BASE[@]}" "${LEGIT[@]}" run --rm -T client \
  bash -c 'ssh-keyscan -t ed25519 172.28.0.10 2>/dev/null \
           | sed "s|^172.28.0.10|sokrates-vm|" > /work/known_host.pub \
           && echo "--- known_host.pub ---" \
           && cat /work/known_host.pub'

separator "Escenario A | trafico LEGITIMO + cliente VULNERABLE"
echo "Esperado: lee 'datos confidenciales del pharma pipeline'."
docker compose "${COMPOSE_BASE[@]}" "${LEGIT[@]}" run --rm -T client \
  python /work/client/client_vulnerable.py

separator "Escenario B | MITM + cliente VULNERABLE  <-- EL ATAQUE"
echo "Esperado: AutoAddPolicy() acepta sin avisar, manda la password al atacante."
docker compose "${COMPOSE_BASE[@]}" "${EVIL[@]}" run --rm -T client \
  python /work/client/client_vulnerable.py
echo
echo "--- /var/log/stolen.log en evil-server (credenciales capturadas) ---"
docker compose "${COMPOSE_BASE[@]}" exec -T evil-server cat /var/log/stolen.log

separator "Escenario C | MITM + cliente SEGURO  <-- DEFENSA"
echo "Esperado: BadHostKeyException o 'not found in known_hosts'. NO se envia la password."
BEFORE=$(docker compose "${COMPOSE_BASE[@]}" exec -T evil-server wc -l < /var/log/stolen.log | tr -d '[:space:]')
docker compose "${COMPOSE_BASE[@]}" "${EVIL[@]}" run --rm -T client \
  python /work/client/client_secure.py || true
AFTER=$(docker compose "${COMPOSE_BASE[@]}" exec -T evil-server wc -l < /var/log/stolen.log | tr -d '[:space:]')
echo
echo "Lineas en stolen.log antes=${BEFORE}, despues=${AFTER}"
if [ "$BEFORE" = "$AFTER" ]; then
  echo "OK: paramiko aborto antes de auth, no hay nuevas credenciales robadas."
else
  echo "MAL: se ha registrado una linea nueva en stolen.log."
fi

separator "Escenario D | trafico LEGITIMO + cliente SEGURO"
echo "Esperado: lee el fichero, demuestra que la version segura no rompe el caso bueno."
docker compose "${COMPOSE_BASE[@]}" "${LEGIT[@]}" run --rm -T client \
  python /work/client/client_secure.py

separator "Fin. Para parar todo: docker compose down -v"
