#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

function usage() {
  cat <<EOF
Usage: $0 {install|deploy|backup|monitoring}

Commands:
  install    Install Docker, UFW, fail2ban, Helm, and bootstrap the server
  deploy     Build and start the Docker Compose stack
  backup     Export PostgreSQL and Redis backups
  monitoring Install optional Kubernetes monitoring via Helm
EOF
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

case "$1" in
  install)
    sudo bash deploy/install-server.sh
    ;;
  deploy)
    bash deploy/deploy.sh
    ;;
  backup)
    bash deploy/backup.sh
    ;;
  monitoring)
    if [[ -x "$(pwd)/k8s-monitoring/install-monitoring.sh" ]]; then
      bash k8s-monitoring/install-monitoring.sh
    else
      echo "Monitoring installer not found."
      exit 1
    fi
    ;;
  *)
    usage
    exit 1
    ;;
esac
