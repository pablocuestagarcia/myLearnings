#!/usr/bin/env bash
# Instala NATS con JetStream habilitado usando el chart oficial.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Añadiendo el repo nats"
helm repo add nats https://nats-io.github.io/k8s/helm/charts/ >/dev/null
helm repo update nats >/dev/null

echo "==> Instalando NATS en el namespace nats"
helm upgrade --install nats nats/nats \
  --namespace nats --create-namespace \
  -f "${SCRIPT_DIR}/nats-values.yaml" \
  --wait --timeout 3m

echo "==> Estado"
kubectl -n nats get pods,svc
