#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v helm >/dev/null 2>&1; then
  echo "Helm is required. Install it and re-run this script."
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required. Install it and re-run this script."
  exit 1
fi

echo "Adding Grafana Helm repository..."
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

echo "Installing Loki stack..."
helm upgrade --install loki-stack grafana/loki-stack \
  -f loki-values.yaml \
  --namespace monitoring --create-namespace

echo "Installing kube-prometheus-stack..."
helm upgrade --install kube-prometheus-stack grafana/kube-prometheus-stack \
  -f prometheus-values.yaml \
  --namespace monitoring

echo "Monitoring stack installed."

echo "Use 'kubectl get pods -n monitoring' to verify."
