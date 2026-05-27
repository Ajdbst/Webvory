#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "This script must be run as root or with sudo."
  exit 1
fi

echo "[1/11] Updating package index and installing dependencies..."
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release software-properties-common ufw fail2ban openssl git

if ! command -v docker >/dev/null 2>&1; then
  echo "[2/11] Installing Docker..."
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
fi

if ! command -v helm >/dev/null 2>&1; then
  echo "[3/11] Installing Helm..."
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "[4/11] Installing kubectl..."
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
  rm -f kubectl
fi

if command -v helm >/dev/null 2>&1; then
  echo "[5/11] Initializing Helm repositories..."
  helm repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
  helm repo update
fi

USER_NAME=${SUDO_USER:-$(whoami)}
if id -nG "$USER_NAME" | grep -qw docker; then
  echo "User $USER_NAME is already in docker group."
else
  usermod -aG docker "$USER_NAME"
  echo "Added $USER_NAME to docker group. Log out and log back in to use Docker without sudo."
fi

echo "[6/11] Enabling UFW and opening required ports..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose

echo "[7/11] Configuring fail2ban..."
cat > /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 600
EOF
systemctl restart fail2ban

echo "[8/11] Creating deployment directories..."
cd /opt || true
mkdir -p /opt/webvory
mkdir -p /opt/webvory/deploy/ssl
chown -R "$USER_NAME":"$USER_NAME" /opt/webvory

echo "[9/11] Creating self-signed SSL certificate fallback..."
SSL_DIR=/opt/webvory/deploy/ssl
mkdir -p "$SSL_DIR"
if [[ ! -f "$SSL_DIR/server.key" || ! -f "$SSL_DIR/server.crt" ]]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/CN=localhost/O=Webvory/"
fi

echo "[10/11] Preparing deployment helper scripts..."
cd /opt/webvory
cat > deploy/setup-environment.sh <<'EOF'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Please update .env before deploying."
fi
EOF
chmod +x deploy/setup-environment.sh

cat > deploy/deploy.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cp .env.example .env 2>/dev/null || true
export COMPOSE_HTTP_TIMEOUT=200
/usr/bin/docker compose pull || true
/usr/bin/docker compose up -d --build
/usr/bin/docker compose ps
EOF
chmod +x deploy/deploy.sh

cat > deploy/backup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
BACKUP_DIR="$(pwd)/backups"
mkdir -p "$BACKUP_DIR"
source .env
TIMESTAMP=$(date +"%F_%H%M%S")
/usr/bin/docker exec -t webvory_postgres pg_dumpall -U "$POSTGRES_USER" > "$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql"
/usr/bin/docker exec -t webvory_redis redis-cli save
cp -r /var/lib/redis/dump.rdb "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb" 2>/dev/null || true
echo "Backups created in $BACKUP_DIR"
EOF
chmod +x deploy/backup.sh

echo "[11/11] Initializing repository skeleton in /opt/webvory..."
if [[ ! -d /opt/webvory/.git ]]; then
  cd /opt/webvory
  git init
fi

echo "[11/11] Server bootstrap script installed. Run 'cd /opt/webvory && ./deploy/deploy.sh' after you copy the repository content."
