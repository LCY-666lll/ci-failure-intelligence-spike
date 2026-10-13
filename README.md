# CI Failure Deployment Feasibility Spike

This repository validates a zero-cost deployment path for a Python AI application. It is intentionally small and proves the risky infrastructure boundaries before the full project is built.

## Public proof

- Service: https://ci-failure-intelligence-spike.onrender.com
- Readiness: https://ci-failure-intelligence-spike.onrender.com/health/ready
- Persisted CI run: https://ci-failure-intelligence-spike.onrender.com/api/v1/ci-runs/1
- GitHub Actions run: https://github.com/LCY-666lll/ci-failure-intelligence-spike/actions/runs/38415959319
- Validation report: [docs/local-validation-report.md](docs/local-validation-report.md)

The Render Free web service sleeps after inactivity, so the first request can take longer. The validation database is a time-limited free instance and is not the final production database choice.

## Local run

```bash
docker compose up --build -d
curl http://localhost:8000/health/ready
```

The API container is restricted to 512 MB to match the target free web-service limit.

