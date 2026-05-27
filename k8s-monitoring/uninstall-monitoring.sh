#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v helm >/dev/null 2>&1; then
  echo "Helm is required. Install it and re-run this script."
  exit 1
fi

echo "Uninstalling kube-prometheus-stack..."
helm uninstall kube-prometheus-stack --namespace monitoring || true

echo "Uninstalling loki-stack..."
helm uninstall loki-stack --namespace monitoring || true

echo "Removing monitoring namespace..."
kubectl delete namespace monitoring --ignore-not-found

echo "Monitoring stack removed."
