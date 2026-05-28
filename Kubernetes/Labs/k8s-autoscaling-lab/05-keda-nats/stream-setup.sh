#!/usr/bin/env bash
# Crea el stream ORDERS y el consumer durable 'workers' usando nats-box.
#
# nats-box es una imagen oficial con el CLI 'nats'. Lanzamos un pod
# efímero, ejecutamos los comandos y lo borramos al salir.
#
# El flag --defaults indica al CLI que use valores por defecto para
# cualquier opción no especificada, en lugar de pedirla por prompt
# (esto es imprescindible al ejecutar sin TTY).
set -euo pipefail

NATS_URL="nats://nats.nats.svc.cluster.local:4222"

echo "==> Creando stream ORDERS y consumer workers"
kubectl -n nats run nats-box-setup --rm -i --restart=Never \
  --image=natsio/nats-box:latest -- sh -c "
set -e

nats --server=${NATS_URL} stream add ORDERS \
  --subjects='orders.>' \
  --storage=file \
  --retention=limits \
  --replicas=1 \
  --defaults

nats --server=${NATS_URL} consumer add ORDERS workers \
  --pull \
  --ack=explicit \
  --deliver=all \
  --defaults

echo '--- Streams ---'
nats --server=${NATS_URL} stream ls
echo '--- Consumers del stream ORDERS ---'
nats --server=${NATS_URL} consumer ls ORDERS
"
