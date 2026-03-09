# 🛡️ CodeGuardian – AI-Powered Code Review Assistant

[![CI](https://github.com/lasithahemajith/Code-Guardian-X/actions/workflows/ci.yml/badge.svg)](https://github.com/lasithahemajith/Code-Guardian-X/actions/workflows/ci.yml)

A production-ready **event-driven microservices platform** that automatically performs AI-powered code reviews for GitHub and GitLab pull requests.

## Architecture

```
GitHub/GitLab Webhook
         │
         ▼
  ┌─────────────────┐
  │  repo-service   │  Ingests PR webhooks, verifies HMAC-SHA256 signatures
  └────────┬────────┘
           │ Kafka: pr.events
           ▼
  ┌─────────────────────┐
  │  analysis-service   │  Extracts git diff, prepares per-file code payloads
  └──────────┬──────────┘
             │ Kafka: code.analysis.ready
    ┌────────┴────────┐
    ▼                 ▼
┌─────────┐   ┌──────────────────┐
│ai-service│   │static-analysis   │  Parallel analysis
│ (LLM)   │   │(bandit/pylint/   │
└────┬─────┘  │ semgrep)        │
     │         └────────┬────────┘
     │ ai.review.       │ static.analysis.
     │ completed        │ completed
     └────────┬─────────┘
              ▼
   ┌──────────────────────┐
   │  review-aggregator   │  Merges, deduplicates, ranks by severity (Redis)
   └──────────┬───────────┘
              │ Kafka: review.finalized
              ▼
   ┌───────────────────────┐
   │  notification-service │  GitHub PR comments, Slack, Email
   └───────────────────────┘

   ┌─────────────────┐        ┌──────────────┐
   │   api-gateway   │◄───────│   frontend   │  Next.js dashboard
   │ (JWT/REST/DB)   │        │ (Next.js)    │
   └─────────────────┘        └──────────────┘

   ┌──────────────────┐      ┌────────────────────┐
   │  metrics-service │─────►│ Prometheus/Grafana │
   └──────────────────┘      └────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api-gateway` | 8000 | JWT auth, RBAC, REST API, PostgreSQL |
| `repo-service` | 8001 | GitHub/GitLab webhooks |
| `analysis-service` | 8002 | Git diff extraction |
| `ai-service` | 8003 | Rule-based + optional OpenAI analysis |
| `static-analysis` | 8004 | bandit, pylint, semgrep |
| `review-aggregator` | 8005 | Redis-backed result merger |
| `notification-service` | 8006 | PR comments, Slack, Email |
| `metrics-service` | 8007 | Prometheus metrics |
| `frontend` | 3000 | Next.js dashboard |
| `prometheus` | 9090 | Metrics scraping |
| `grafana` | 3001 | Dashboards |

## Kafka Topics

| Topic | Producer | Consumers |
|-------|----------|-----------|
| `pr.events` | repo-service | analysis-service |
| `code.analysis.ready` | analysis-service | ai-service, static-analysis |
| `ai.review.completed` | ai-service | review-aggregator |
| `static.analysis.completed` | static-analysis | review-aggregator |
| `review.finalized` | review-aggregator | notification-service |

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- A `JWT_SECRET_KEY` environment variable (required, no default)

### 1. Clone and configure

```bash
git clone https://github.com/lasithahemajith/Code-Guardian-X.git
cd Code-Guardian-X
cp frontend/.env.local.example frontend/.env.local
```

### 2. Set required environment variable

```bash
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
```

### 3. Start the platform

```bash
docker compose up -d
```

### 4. Access services

- **Frontend dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin / admin)

### 5. Login to the API

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123"
```

Demo users: `admin/admin123` (admin) · `developer/dev123` (developer)

## Configuring Webhooks

### GitHub

1. In your GitHub repo: **Settings → Webhooks → Add webhook**
2. Payload URL: `http://your-server:8001/webhooks/github`
3. Content type: `application/json`
4. Events: Pull requests

### GitLab

1. In your GitLab project: **Settings → Webhooks**
2. URL: `http://your-server:8001/webhooks/gitlab`
3. Events: Merge request events

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | api-gateway | **Required**. JWT signing key |
| `OPENAI_API_KEY` | ai-service | Optional. Enables GPT-4 analysis |
| `OPENAI_MODEL` | ai-service | Default: `gpt-4` |
| `GITHUB_TOKEN` | notification-service | For posting PR comments |
| `SLACK_WEBHOOK_URL` | notification-service | Slack notifications |
| `NOTIFY_EMAIL_TO` | notification-service | Email recipient |
| `REDIS_RESULT_TTL` | review-aggregator | TTL for partial results (default: 86400) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | api-gateway | JWT expiry (default: 60) |
| `POSTGRES_PASSWORD` | postgres | DB password (default: codeguardian) |

## Testing

### Backend (per service)

```bash
cd services/api-gateway
pip install -r requirements.txt
pytest tests/ -v
```

### All services at once

```bash
for svc in api-gateway repo-service analysis-service ai-service static-analysis review-aggregator notification-service; do
  echo "=== $svc ==="
  cd services/$svc && pytest tests/ -q && cd -
done
```

### Integration tests

```bash
pip install -r services/analysis-service/requirements.txt \
            -r services/ai-service/requirements.txt \
            -r services/review-aggregator/requirements.txt
pytest tests/integration/ -v
```

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm test
```

### Lint

```bash
pip install flake8
flake8 services/ --max-line-length=120
```

## AI Analysis

By default, the ai-service uses **rule-based analysis** detecting:
- SQL injection patterns (string concatenation in queries)
- Hardcoded credentials/secrets
- `eval()` usage
- Infinite loops (`while True:` without `break`)
- Missing error handling

Set `OPENAI_API_KEY` to enable **GPT-4 analysis** with detailed explanations and suggestions.

## Security

- JWT authentication with configurable expiry
- HMAC-SHA256 webhook signature verification
- RBAC roles: `admin`, `developer`, `viewer`
- No hardcoded secrets — all configuration via environment variables
- `JWT_SECRET_KEY` has no default (required)

## Kubernetes Deployment

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/kafka.yml
kubectl apply -f k8s/api-gateway.yml
kubectl apply -f k8s/repo-service.yml
```

Create secrets first:
```bash
kubectl create secret generic codeguardian-secrets \
  --namespace codeguardian \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=database-url="postgresql://..." \
  --from-literal=postgres-password="$(openssl rand -hex 16)"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests: `pytest tests/ -v`
4. Submit a pull request

## License

MIT
