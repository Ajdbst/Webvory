# Webvory AI Backend

A production-ready FastAPI backend with Docker Compose, PostgreSQL, Redis, NGINX, and optional Kubernetes monitoring.

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd Webvory
   cp .env.example .env
   ```

2. **Update `.env` with your values**:
   ```bash
   # Required secrets
   SECRET_KEY=your-secure-key
   POSTGRES_PASSWORD=your-db-password
   ```

3. **Start the stack**:
   ```bash
   docker compose up -d
   ```

4. **Verify services**:
   ```bash
   curl http://localhost/
   curl http://localhost/health
   curl -X POST http://localhost/predict -H "Content-Type: application/json" -d '{"prompt": "test"}'
   ```

5. **View logs**:
   ```bash
   docker compose logs -f web
   ```

6. **Stop and cleanup**:
   ```bash
   docker compose down
   ```

## Production Deployment (GitHub Actions)

### Prerequisites

- A target Ubuntu/Debian server with SSH access
- GitHub repository with Admin or Secrets permissions

### Setup GitHub Secrets

Add these secrets to **Settings > Secrets and variables > Actions**:

**Required:**
- `SSH_HOST` — Target server IP/hostname
- `SSH_USERNAME` — SSH user (e.g., ubuntu, root)
- `SSH_KEY` — Private SSH key (PEM format)
- `SSH_PORT` — SSH port (default: 22)
- `SSH_DEPLOY_PATH` — Remote deployment path (e.g., `/opt/webvory`)
- `SECRET_KEY` — FastAPI application secret key
- `POSTGRES_USER` — Database username (e.g., webvory)
- `POSTGRES_PASSWORD` — Strong database password
- `POSTGRES_DB` — Database name (e.g., webvory)

**Optional:**
- `APP_ENV` — Application environment (default: production)
- `LOG_LEVEL` — Logging level (default: INFO)
- `SSL_DOMAIN` — Domain for SSL certificates
- `REDIS_HOST` — Redis hostname (default: redis)
- `REDIS_PORT` — Redis port (default: 6379)
- `DEPLOY_PATH` — Deployment path (default: /opt/webvory)

### Deployment Flow

1. Push to `main` branch → GitHub Actions workflow triggers
2. Workflow validates Python syntax and Docker Compose config
3. Syncs repository to target server via SCP
4. Runs `deploy/install-server.sh` (installs Docker, Helm, kubectl, UFW, fail2ban)
5. Runs `deploy/deploy.sh` (starts Docker Compose stack)

### Verify Remote Deployment

```bash
ssh user@target-server
cd /opt/webvory
docker compose ps
docker compose logs -f web
```

## Architecture

See [architecture.md](architecture.md) for detailed diagrams and component descriptions.

### Docker Compose Stack

```
NGINX (reverse proxy, TLS termination)
  ↓
FastAPI (web backend, 8000)
  ↓
PostgreSQL (database, port 5432)
Redis (cache, port 6379)
```

- **NGINX**: Handles HTTP→HTTPS redirect, TLS termination, proxies to FastAPI
- **FastAPI**: Serves `/health`, `/ready`, `/predict` endpoints
- **PostgreSQL**: Persistent data storage (15-alpine)
- **Redis**: Session cache and fast KV store (7-alpine)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|----------|
| `/` | GET | Service info |
| `/health` | GET | Health check (includes Redis status) |
| `/ready` | GET | Readiness probe |
| `/predict` | POST | AI completion endpoint |

### Example Requests

**Health Check**:
```bash
curl http://localhost/health
```

**Prediction**:
```bash
curl -X POST http://localhost/predict \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "max_tokens": 256}'
```

## Maintenance

### Backup Database

On the remote server:
```bash
cd /opt/webvory
bash deploy/backup.sh
```

Backups saved to `./backups/`

### View Logs

```bash
cd /opt/webvory
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f redis
```

### Restart Services

```bash
cd /opt/webvory
docker compose restart
```

### Pull Latest Images

```bash
cd /opt/webvory
docker compose pull && docker compose up -d --build
```

## Optional Kubernetes Monitoring

For clusters running Kubernetes:

```bash
cd k8s-monitoring
chmod +x install-monitoring.sh
./install-monitoring.sh
```

Installs:
- **Prometheus** — Metrics collection and alerting
- **Grafana** — Dashboard and visualization
- **Loki** — Log aggregation
- **Promtail** — Log shipper

See [k8s-monitoring/README.md](k8s-monitoring/README.md) for details.

## Troubleshooting

### Docker not found on remote server

```bash
# Manually run the bootstrap
ssh user@target-server
cd /opt/webvory
sudo bash deploy/install-server.sh
```

### Missing .env file

The deploy script will copy from `.env.example` if `.env` is missing:
```bash
cd /opt/webvory
cp .env.example .env
# Edit .env with actual secrets
docker compose up -d
```

### Port conflicts

Default ports:
- 80 → HTTP
- 443 → HTTPS
- 5432 → PostgreSQL (internal only)
- 6379 → Redis (internal only)

### Certificate issues

Self-signed certificates are generated in `deploy/ssl/` during bootstrap. For production, use Let's Encrypt:

```bash
# Create certificates manually
sudo certbot certonly --standalone -d yourdomain.com
# Copy to deploy/ssl/
```

## Project Structure

```
Webvory/
├── .github/workflows/
│   └── deploy.yml                 # CI/CD pipeline
├── app/
│   ├── main.py                    # FastAPI application
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Container image
├── config/
│   └── nginx/
│       └── default.conf            # NGINX config
├── deploy/
│   ├── install-server.sh           # Bootstrap server (Docker, Helm, etc.)
│   ├── deploy.sh                   # Deploy Docker Compose stack
│   ├── backup.sh                   # Backup database and cache
│   └── ssl/                        # SSL certificates (gitignored)
├── k8s-monitoring/                 # Optional Kubernetes monitoring
│   ├── install-monitoring.sh
│   ├── prometheus-values.yaml
│   └── loki-values.yaml
├── docker-compose.yml              # Service definitions
├── .env.example                    # Example environment variables
├── architecture.md                 # Deployment architecture
└── README.md                       # This file
```

## Security Notes

- ✅ `.env` is gitignored—secrets never committed
- ✅ NGINX enforces HTTPS with modern TLS (1.2+)
- ✅ PostgreSQL is only accessible within Docker network
- ✅ Redis is only accessible within Docker network
- ✅ UFW firewall configured to allow only 22, 80, 443
- ✅ fail2ban protects SSH from brute force
- ⚠️ Replace self-signed certificates before production
- ⚠️ Rotate `SECRET_KEY` regularly

## License

DevOps Assignment
