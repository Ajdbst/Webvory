# Architecture Overview

This deployment uses a simple, production-oriented container architecture for a VPS-based application.

```
                    Internet
                       |
                   [NGINX]
                       |
    +------------------+------------------+
    |                  |                  |
[FastAPI]        [PostgreSQL]         [Redis]
    |                  |                  |
    +------------------+------------------+
         Docker Compose internal network
```

- NGINX handles TLS termination and reverse proxying into the FastAPI service.
- FastAPI is the backend API container, serving health, readiness, and predict endpoints.
- PostgreSQL stores persistent application data securely behind the private Docker network.
- Redis provides a fast cache/session store and a health dependency for service readiness.
- GitHub Actions builds and deploys code to the target server via SSH.

## Optional Kubernetes monitoring architecture

When using a Kubernetes cluster for observability, the following optional stack is supported:

```
Kubernetes cluster
   |-- Grafana Loki (logs)
   |-- Prometheus + Alertmanager (metrics)
   |-- Grafana (dashboards)
```

This is implemented with Helm charts:

- `loki-stack` for log aggregation and Promtail
- `kube-prometheus-stack` for metrics, alerts, and Grafana dashboards
