# Maize Monitor Platform

A small maize monitoring service built on open data, run like a production
service: containerized, tested and built by a pipeline, deployed to Kubernetes,
provisioned with Terraform, and monitored.

Inspired by operational crop monitoring services. Not affiliated with any company or project.

## Status

| Phase | Topic | State |
| --- | --- | --- |
| 1 | Science core with real data | To do (sample data is synthetic) |
| 2 | Web API | Starter done |
| 3 | Docker | Starter done |
| 4 | CI pipeline | Starter done |
| 5 | Kubernetes (local) | To do |
| 6 | Terraform and Azure | To do |
| 7 | Monitoring | To do |
| 8 | Incident report and docs | To do |

## Run it

With Python:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload
```

With Docker:

```bash
docker compose up --build
```

Then open http://localhost:8000/docs

## Endpoints

| Path | Returns |
| --- | --- |
| `/health` | Service status |
| `/regions` | Available regions |
| `/estimate/{region_id}` | NDVI time series and yield estimate |

## Layout

```
app/        API (main.py) and science core (core.py)
tests/      Unit and API tests
deploy/     Kubernetes Helm chart (phase 5)
infra/      Terraform for Azure (phase 6)
monitoring/ Dashboards and alert rules (phase 7)
docs/       Diagram, runbook, incident report (phase 8)
```

## Known limits

- The sample data is synthetic. The yield model is a placeholder and is not fitted to real statistics.
