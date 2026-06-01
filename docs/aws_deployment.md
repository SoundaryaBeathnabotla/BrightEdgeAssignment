# Public Deployment Guide

This project can be deployed to AWS, GCP, or Azure. The most practical AWS options are App Runner, Elastic Beanstalk, or ECS/Fargate. For an assessment demo, App Runner is the cleanest path because it can build from a GitHub repository and expose a public HTTPS URL with minimal infrastructure work.

## Recommended AWS Option: App Runner

### 1. Prepare The Project

From the project folder:

```powershell
cd C:\Users\sound\OneDrive\Documents\bright_EDGE
python -m unittest discover -s tests -v
```

Confirm these files exist:

```text
Dockerfile
README.md
app/api.py
docs/architecture.md
docs/schema.md
docs/poc_release_plan.md
docs/presentation.md
```

### 2. Push To GitHub

Create a GitHub repository, then push this project. See the GitHub section below.

### 3. Create App Runner Service

In AWS Console:

1. Open **AWS App Runner**.
2. Click **Create service**.
3. Choose **Source code repository**.
4. Connect GitHub and select your repository.
5. Branch: `main`.
6. Deployment trigger: automatic or manual.
7. Runtime/source type: use Dockerfile from repository.
8. Port: `8000`.
9. Environment variables:
   - `HOST=0.0.0.0`
   - `PORT=8000`
10. Instance size: start small, for example 0.25 vCPU / 0.5 GB memory.
11. Create service.

App Runner will build the Docker image, start the service, and provide a public HTTPS URL.

### 4. Test The Public URL

Open:

```text
https://your-app-runner-url/
```

Then test:

```text
https://your-app-runner-url/crawl?url=https%3A%2F%2Fexample.com
```

PowerShell API test:

```powershell
curl -Method POST https://your-app-runner-url/crawl -ContentType "application/json" -Body '{"url":"https://example.com","include_body_text":false}'
```

### 5. What To Submit

Send:

- GitHub repository URL.
- Public App Runner URL.
- Short note that `/` is the clean browser demo and `/crawl` is the API endpoint.
- Mention that some origins may block crawlers with 403 and the app reports that as a structured error.

## Alternative AWS Option: Elastic Beanstalk

Elastic Beanstalk can run the Python app using the included `Procfile`.

High-level steps:

1. Install AWS CLI and EB CLI.
2. Configure AWS credentials:

```powershell
aws configure
```

3. Initialize Elastic Beanstalk:

```powershell
eb init
```

Choose:

- Platform: Python
- Region: your preferred AWS region
- Application name: `brightedge-crawler`

4. Create environment:

```powershell
eb create brightedge-crawler-prod
```

5. Open the deployed app:

```powershell
eb open
```

6. Deploy updates:

```powershell
eb deploy
```

For a candidate assignment, App Runner is usually simpler than Elastic Beanstalk.

## Production AWS Architecture

The public demo deploys one synchronous service. The billion-URL design should use a distributed architecture:

| Layer | AWS Service |
| --- | --- |
| Monthly input files | S3 |
| MySQL source ingest | AWS DMS or Glue JDBC |
| Batch normalization/dedupe | Glue, EMR, or Athena |
| URL queue | SQS or MSK |
| Domain rate limit store | DynamoDB or ElastiCache Redis |
| Crawler workers | ECS/Fargate, EKS, or Batch |
| Raw event/body storage | S3 with Parquet/JSONL and lifecycle policies |
| Serving metadata | DynamoDB, Aurora, or OpenSearch |
| Monitoring | CloudWatch, OpenTelemetry, Prometheus/Grafana |

## GCP Equivalent

| AWS | GCP |
| --- | --- |
| App Runner / ECS | Cloud Run |
| S3 | Cloud Storage |
| SQS / MSK | Pub/Sub |
| DynamoDB | Firestore / Bigtable |
| Glue / EMR | Dataproc / Dataflow |
| CloudWatch | Cloud Monitoring |

For a quick GCP demo, deploy the Dockerfile to Cloud Run and set port `8000`.

## Azure Equivalent

| AWS | Azure |
| --- | --- |
| App Runner / ECS | Azure Container Apps |
| S3 | Blob Storage |
| SQS / MSK | Service Bus / Event Hubs |
| DynamoDB | Cosmos DB |
| Glue / EMR | Synapse / Databricks |
| CloudWatch | Azure Monitor |

For a quick Azure demo, deploy the Dockerfile to Azure Container Apps.

## GitHub Push Commands

If this folder is not already connected to GitHub:

```powershell
cd C:\Users\sound\OneDrive\Documents\bright_EDGE
git init
git add .
git commit -m "BrightEdge crawler assessment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If the remote already exists:

```powershell
git add .
git commit -m "BrightEdge crawler assessment"
git push
```

Do not commit local output files such as `crawl_results.jsonl`; `.gitignore` excludes them.
