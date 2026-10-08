# Maize Monitor Platform

A small maize monitoring service built on open data, run like a production
service: containerized, tested and built by a pipeline, deployed to Kubernetes
with Helm, and updated by a weekly scheduled job.

Inspired by operational crop monitoring services. Not affiliated with any company or project.

## Status

| Phase | Topic | State |
| --- | --- | --- |
| 1 | Science core with real data | To do (sample data is synthetic) |
| 2 | Web API | Done |
| 3 | Docker | Done |
| 4 | CI pipeline (lint, tests, Helm lint, image build and push) | Done |
| 5 | Kubernetes with Helm, weekly CronJob, image from registry | Done (local cluster) |
| 6 | Terraform and Azure | To do |
| 7 | Monitoring | To do |
| 8 | Incident report and docs | To do |

## How it fits together

1. A push to `main` runs the pipeline: lint, tests, Helm chart check.
2. If they pass, the pipeline builds the Docker image and publishes it to
   `ghcr.io/margaretjohn14-alt/maize-monitor-platform`, tagged with the commit ID.
3. Helm installs the chart on a Kubernetes cluster, which pulls that image:
   - an API with 2 replicas and health checks
   - a CronJob that runs the data update every Monday at 06:00 UTC

   
## Run it

### Option 1: Python only

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs

### Option 2: Docker

```bash
docker compose up --build
```

Open http://localhost:8000/docs

### Option 3: Kubernetes (local cluster with kind and Helm)

Requires Docker, [kind](https://kind.sigs.k8s.io/), kubectl and [Helm](https://helm.sh/).

```bash
kind create cluster --name maize
helm install maize-monitor deploy/helm/maize-monitor --set image.tag=<commit ID>
kubectl get pods,cronjobs
kubectl port-forward service/maize-monitor 8080:80
```

Open http://localhost:8080/docs

Use the ID of a commit whose pipeline run is green; that commit has a published image.

Run the weekly update by hand:

```bash
kubectl create job --from=cronjob/maize-monitor-update manual-run
kubectl logs job/manual-run
```

Remove everything:

```bash
kind delete cluster --name maize
```

## Endpoints

| Path | Returns |
| --- | --- |
| `/health` | Service status |
| `/version` | Running version |
| `/regions` |