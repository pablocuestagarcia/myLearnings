#!/usr/bin/env bash
# Instala metrics-server y le aplica el parche necesario para kind:
# kubelet usa certificados self-signed, así que añadimos --kubelet-insecure-tls.
set -euo pipefail

echo "==> Aplicando manifests oficiales de metrics-server"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo "==> Parche --kubelet-insecure-tls (necesario en kind)"
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

echo "==> Esperando a que metrics-server esté listo"
kubectl -n kube-system rollout status deployment/metrics-server --timeout=180s

echo "==> Test rápido"
sleep 20  # da margen para que recopile la primera muestra
kubectl top nodes
