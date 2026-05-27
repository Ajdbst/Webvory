# Kubernetes Monitoring - Helm Charts

This folder contains optional monitoring deployment examples using Helm charts for a Kubernetes cluster.

## What is included

- `loki-values.yaml` — values for Grafana Loki stack with Promtail log collection
- `prometheus-values.yaml` — values for kube-prometheus-stack monitoring + Grafana
- `install-monitoring.sh` — script to install Helm charts into a cluster
- `uninstall-monitoring.sh` — script to remove the installed monitoring stack

## Prerequisites

- A Kubernetes cluster accessible via `kubectl`
- `helm` installed and configured
- Cluster access for installing CRDs and services

## Install monitoring stack

```bash
cd k8s-monitoring
chmod +x install-monitoring.sh
./install-monitoring.sh
```

## Uninstall monitoring stack

```bash
chmod +x uninstall-monitoring.sh
./uninstall-monitoring.sh
```

## Notes

- `loki-stack` is used for log aggregation and Promtail log collection.
- `kube-prometheus-stack` provides Prometheus, Alertmanager, and Grafana.
- Use `kubectl port-forward` or a LoadBalancer service to access Grafana.
