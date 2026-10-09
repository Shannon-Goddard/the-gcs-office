# AWS Setup — GC Office Verify Backend

Everything needed to rebuild the verification backend from scratch.

---

## Account & Region

| | |
|---|---|
| AWS Account ID | `<your-aws-account-id>` |
| Region | `us-east-1` |
| IAM | Root credentials used — consider creating a least-privilege deploy user for CI |

---

## SSM Parameter Store

Bright Data CDP URL is stored as a **SecureString** — never in code or env files.

```bash
aws ssm put-parameter \
  --name "/gcoffice/brightdata_sb_url" \
  --value "wss://<brightdata-customer-id>-zone-<zone-name>:<password>@brd.superproxy.io:9222" \
  --type SecureString \
  --region us-east-1
```

SAM reads it at deploy time via `--parameter-overrides`. It is marked `NoEcho: true` in `template.yaml` so it never appears in CloudFormation console output.

---

## DynamoDB

**Table name**: `gcoffice-subs`  
**Billing**: PAY_PER_REQUEST  
**Primary key**: `pk` (String) + `sk` (String)

| Key pattern | Example |
|---|---|
| `pk` | `STATE#CA` |
| `sk` | `LICENSE#926325` |

**GSI**: `zip-trade-index`

| Attribute | Value |
|---|---|
| Partition key | `gsi_zip_trade` (String) |
| Example value | `ZIP#92504#TRADE#plumbing` |
| Projection | ALL |

### Create table

```bash
aws dynamodb create-table \
  --table-name gcoffice-subs \
  --attribute-definitions \
      AttributeName=pk,AttributeType=S \
      AttributeName=sk,AttributeType=S \
      AttributeName=gsi_zip_trade,AttributeType=S \
  --key-schema \
      AttributeName=pk,KeyType=HASH \
      AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[{
    "IndexName": "zip-trade-index",
    "KeySchema": [{"AttributeName":"gsi_zip_trade","KeyType":"HASH"}],
    "Projection": {"ProjectionType":"ALL"}
  }]' \
  --region us-east-1
```

### Seed

```bash
python scripts/seed_subs.py
```

Reads `data/ca/ca_licensed_contractors.csv` (275,390 rows). Computes `is_bonded` and `is_wc_covered` at seed time. Uses `batch_writer` — takes ~17 minutes on a standard connection.

---

## ECR

**Repo name**: `gcoffice-verify`

```bash
# Create repo
aws ecr create-repository --repository-name gcoffice-verify --region us-east-1

# Authenticate
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build — must be linux/amd64 single-arch, provenance=false or Lambda rejects it
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  -t <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/gcoffice-verify:latest \
  --push \
  lambda/
```

> **Gotcha**: Default Docker Desktop builds a multi-arch manifest list. Lambda only accepts a single-arch image digest. `--provenance=false` suppresses the attestation manifest that triggers the rejection.

---

## Lambda + API Gateway (SAM)

**Stack name**: `gcoffice-verify`  
**Template**: `template.yaml`

Three functions in one container image:

| Function | Handler | Route |
|---|---|---|
| `VerifyLicense` | `verify-license/handler.lambda_handler` | `POST /api/verify-license` |
| `VerifyBond` | `verify-bond/handler.lambda_handler` | `POST /api/verify-bond` |
| `VerifyWc` | `verify-wc/handler.lambda_handler` | `POST /api/verify-wc` |

### Deploy

```bash
# First deploy — guided
sam deploy --guided

# Subsequent deploys
sam deploy \
  --stack-name gcoffice-verify \
  --image-repository <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/gcoffice-verify \
  --parameter-overrides BrightDataSbUrl=$(aws ssm get-parameter \
      --name /gcoffice/brightdata_sb_url \
      --with-decryption \
      --query Parameter.Value \
      --output text) \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

> **Note**: SAM does not support `ssm-secure://` dynamic references in Lambda environment variables. The workaround is to resolve the SSM value in the shell and pass it via `--parameter-overrides` at deploy time. The parameter is `NoEcho: true` in the template.

### Live API URL

```
https://<your-api-id>.execute-api.us-east-1.amazonaws.com/prod
```

Set this as the `API_BASE` const at the top of `index.html`.

---

## IAM Permissions needed for deploy

Minimum policies for the deploy principal:

- `AmazonDynamoDBFullAccess` (or scoped to `gcoffice-subs`)
- `AmazonEC2ContainerRegistryFullAccess`
- `AWSLambda_FullAccess`
- `AmazonAPIGatewayAdministrator`
- `AWSCloudFormationFullAccess`
- `IAMFullAccess` (SAM creates execution roles)
- `AmazonSSMReadOnlyAccess`

---

## Cost profile (light usage)

| Service | Free tier | Overage |
|---|---|---|
| DynamoDB | 25 GB + 25 WCU/RCU | ~$0.25/GB/mo |
| Lambda | 1M req/mo | $0.20/1M req |
| API Gateway | 1M req/mo | $3.50/1M req |
| ECR | 500 MB/mo | $0.10/GB |
| Bright Data | Paid plan required | Per GB scraped |

---

## What's never stored

- Bond numbers (matched on page, discarded)
- WC policy numbers
- Bright Data credentials (SSM only)
- `.env` file (gitignored)
