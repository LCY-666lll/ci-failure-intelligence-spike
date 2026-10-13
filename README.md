# CI Failure Deployment Feasibility Spike

This repository validates a zero-cost deployment path for a Python AI application. It is intentionally small and proves the risky infrastructure boundaries before the full project is built.

## Local run

```bash
docker compose up --build -d
curl http://localhost:8000/health/ready
```

The API container is restricted to 512 MB to match the target free web-service limit.

