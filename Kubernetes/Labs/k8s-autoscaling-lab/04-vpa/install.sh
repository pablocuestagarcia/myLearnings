#!/usr/bin/env bash
# Instala el Vertical Pod Autoscaler clonando el repo oficial.
# El script vpa-up.sh genera certificados para el admission webhook y
# despliega: vpa-recommender, vpa-updater y vpa-admission-controller
# en el namespace kube-system.
set -euo pipefail

WORKDIR="$(mktemp -d)"
echo "==> Clonando kubernetes/autoscaler en ${WORKDIR}"
git clone --depth 1 https://github.com/kubernetes/autoscaler.git "${WORKDIR}/autoscaler"

pushd "${WORKDIR}/autoscaler/vertical-pod-autoscaler" >/dev/null

echo "==> Lanzando vpa-up.sh"
./hack/vpa-up.sh

popd >/dev/null

echo "==> Esperando a que los componentes VPA estén Ready"
kubectl -n kube-system rollout status deployment/vpa-recommender --timeout=120s
kubectl -n kube-system rollout status deployment/vpa-updater --timeout=120s
kubectl -n kube-system rollout status deployment/vpa-admission-controller --timeout=120s

echo "==> Verificación"
kubectl get pods -n kube-system | grep vpa
