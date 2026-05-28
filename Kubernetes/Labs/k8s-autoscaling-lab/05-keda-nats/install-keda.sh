#!/usr/bin/env bash
# Instala KEDA con el chart oficial.
set -euo pipefail

echo "==> Añadiendo el repo kedacore"
helm repo add kedacore https://kedacore.github.io/charts >/dev/null
helm repo update kedacore >/dev/null

echo "==> Instalando KEDA en el namespace keda"
helm upgrade --install keda kedacore/keda \
  --namespace keda --create-namespace \
  --wait --timeout 3m

echo "==> Estado"
kubectl -n keda get pods
