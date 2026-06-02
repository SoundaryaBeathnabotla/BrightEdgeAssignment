# AWS Public Deployment Guide

This project was prepared for public demo deployment with **AWS Elastic Beanstalk using Docker**. Elastic Beanstalk is a good fit for this assessment because it can run the included `Dockerfile`, create the EC2 environment, and expose a public URL for reviewers.

The deployed demo is a synchronous crawler API and browser UI. The billion-URL production architecture is still described separately in `docs/architecture.md`.

## 1. Prepare The Project

Run tests before packaging:

```powershell
cd C:\Users\sound\OneDrive\Documents\bright_EDGE
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 10 tests
OK
```

Important deployment files:

```text
Dockerfile
Procfile
README.md
app/
docs/
samples/
tests/
pyproject.toml
```

## 2. Create The Elastic Beanstalk ZIP

Elastic Beanstalk needs `Dockerfile` at the **root** of the ZIP.

Do not upload the GitHub-generated ZIP if it contains a nested folder like:

```text
BrightEdgeAssignment-main/
  Dockerfile
  app/
```

That structure fails because Elastic Beanstalk cannot see `Dockerfile` at the ZIP root.

Correct ZIP root:

```text
Dockerfile
app/
README.md
docs/
```

The clean deployment ZIP is:

```text
C:\Users\sound\OneDrive\Documents\bright_EDGE\brightedge-eb-deploy.zip
```

If it needs to be recreated:

```powershell
cd C:\Users\sound\OneDrive\Documents\bright_EDGE
Compress-Archive -Path .dockerignore,.gitignore,Dockerfile,Procfile,README.md,pyproject.toml,app,docs,samples,tests -DestinationPath brightedge-eb-deploy.zip -Force
```

## 3. Create Elastic Beanstalk Environment

In AWS Console:

1. Open **Elastic Beanstalk**.
2. Click **Create application** or **Create environment**.
3. Environment type:

```text
Web server environment
```

4. Application name:

```text
brightedge-crawler
```

5. Environment name:

```text
brightedge-crawler-prod
```

6. Platform:

```text
Docker running on 64bit Amazon Linux 2023
```

7. Application code:

```text
Upload your code
```

8. Upload:

```text
brightedge-eb-deploy.zip
```

9. Version label:

```text
brightedge-crawler-v1
```

Use `brightedge-crawler-v2`, `v3`, etc. for later uploads.

## 4. Service Access Roles

Elastic Beanstalk needs two IAM roles.

### Service Role

Use or create:

```text
aws-elasticbeanstalk-service-role
```

Trusted entity/use case:

```text
AWS service -> Elastic Beanstalk -> Elastic Beanstalk - Environment
```

Policies commonly used:

```text
AWSElasticBeanstalkEnhancedHealth
AWSElasticBeanstalkManagedUpdatesCustomerRolePolicy
```

### EC2 Instance Profile

Use or create:

```text
aws-elasticbeanstalk-ec2-role
```

Trusted entity/use case:

```text
AWS service -> Elastic Beanstalk -> Elastic Beanstalk - Compute
```

Policies commonly used:

```text
AWSElasticBeanstalkWebTier
AWSElasticBeanstalkWorkerTier
AWSElasticBeanstalkMulticontainerDocker
```

For this web demo, `AWSElasticBeanstalkWebTier` is the most important policy.

## 5. Networking

Use region:

```text
US East (N. Virginia)
```

If there is a default VPC:

1. Select the default VPC.
2. Set public IP address:

```text
Enabled
```

3. Select one or two public subnets.
4. Do not enable a database.

If there is no default VPC, create a simple demo VPC:

```text
Name: brightedge
IPv4 CIDR: 10.0.0.0/16
Availability Zones: 2
Public subnets: 2
Private subnets: 0
NAT Gateway: None
VPC endpoints: None
```

Then return to Elastic Beanstalk, refresh VPCs, select the new VPC, enable public IP, and select the public subnets.

## 6. Instance, Traffic, And Scaling

For a low-cost assessment demo:

```text
Environment type: Single instance
Fleet: On-Demand instance
Architecture: x86_64
Instance type: t3.micro
Root volume: Container default
Monitoring interval: 5 minute
IMDSv1: Disabled
```

If AWS requires two instance types, keep:

```text
t3.micro
t3.small
```

Otherwise keep only:

```text
t3.micro
```

## 7. Monitoring And Logging

For the demo, keep the setup simple:

```text
Health reporting: Enhanced or Basic
CloudWatch custom metrics: none
X-Ray daemon: unchecked
S3 rotate logs: unchecked
CloudWatch log streaming: unchecked
Email notifications: blank
Deployment policy: All at once
Rolling update type: Disabled
Ignore health check: False
Health threshold: Ok
Command timeout: 600
Proxy server: Nginx
```

Managed platform updates can be enabled or disabled. For a short demo, disabling them is simpler.

## 8. Review And Submit

Before clicking **Submit**, verify:

```text
Application: brightedge-crawler
Environment: brightedge-crawler-prod
Platform: Docker running on 64bit Amazon Linux 2023
Application version: brightedge-crawler-v1 or v2
Environment type: Single instance
Instance type: t3.micro
Public IP: Enabled
Service role: aws-elasticbeanstalk-service-role
Instance profile: aws-elasticbeanstalk-ec2-role
```

Click **Submit** and wait 5-10 minutes.

## 9. Fix Common Deployment Error

Error:

```text
Both 'Dockerfile' and 'Dockerrun.aws.json' are missing in your source bundle.
```

Cause:

The uploaded ZIP has a nested folder, or the wrong ZIP was uploaded.

Fix:

Upload:

```text
C:\Users\sound\OneDrive\Documents\bright_EDGE\brightedge-eb-deploy.zip
```

Use a new version label:

```text
brightedge-crawler-v2
```

## 10. Test The Public URL

After deployment, Elastic Beanstalk provides a domain such as:

```text
http://brightedge-crawler-prod.eba-xxxx.us-east-1.elasticbeanstalk.com
```

Current public deployment:

```text
http://brightedge-crawler-prod.eba-pejbg5r3.us-east-1.elasticbeanstalk.com/
```

Open the clean UI:

```text
http://YOUR-ELASTIC-BEANSTALK-DOMAIN/
```

Test the crawler:

```text
http://YOUR-ELASTIC-BEANSTALK-DOMAIN/crawl?url=https%3A%2F%2Fexample.com
```

Current public crawler example:

```text
http://brightedge-crawler-prod.eba-pejbg5r3.us-east-1.elasticbeanstalk.com/crawl?url=https%3A%2F%2Fexample.com
```

Test the API:

```powershell
curl -Method POST http://YOUR-ELASTIC-BEANSTALK-DOMAIN/crawl -ContentType "application/json" -Body '{"url":"https://example.com","include_body_text":false}'
```

## 11. Cost And Cleanup

Elastic Beanstalk itself is not the main cost. It creates AWS resources such as:

- EC2 instance
- Elastic/Public IPv4 address
- EBS volume
- S3 application version storage
- Optional CloudWatch logs/metrics

For one `t3.micro`, a rough 24-hour estimate is about:

```text
$0.35 to $0.45
```

Terminate the environment after demo to avoid ongoing charges:

1. Elastic Beanstalk.
2. Open `brightedge-crawler-prod`.
3. Actions.
4. Terminate environment.
5. Confirm the environment name.

After termination, also check:

- EC2 instances are stopped/terminated.
- Elastic IPs are released if unused.
- S3 Elastic Beanstalk bucket only stores tiny app versions unless manually cleaned.

## 12. What To Submit

Send:

- GitHub repository:

```text
https://github.com/SoundaryaBeathnabotla/BrightEdgeAssignment
```

- Elastic Beanstalk public URL.
- Note that `/` is the clean UI and `/crawl` is the crawler endpoint.
- Note that some origins may return `403 Forbidden`; the service reports those as structured blocked-origin crawl errors.

## Other Cloud Options

The same Dockerfile can be deployed to:

| Cloud | Service |
| --- | --- |
| AWS | Elastic Beanstalk, ECS/Fargate, App Runner if available |
| GCP | Cloud Run |
| Azure | Azure Container Apps |
