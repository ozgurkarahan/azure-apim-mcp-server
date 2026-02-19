# Agent.md — azure-apim-mcp-server

Instructions for AI coding agents working on this codebase.

## Project Overview

Microelectronics semiconductor orders API deployed to Azure Container Apps, exposed through Azure API Management (StandardV2) as both a REST API and MCP (Model Context Protocol) server.

## Architecture

- **REST API flow**: Client → APIM REST API (`/orders/api/v1/*`, subscription key) → Container App (FastAPI) → PostgreSQL
- **MCP flow**: Client → APIM MCP Server (`/st-orders-mcp/mcp`, subscription key, Streamable HTTP) → APIM translates JSON-RPC tool calls into REST API operations → routes through APIM REST API (internal subscription key via `set-header` policy) → Container App → PostgreSQL
- MCP is handled entirely by APIM's native MCP gateway — no custom MCP code on the Container App
- Easy Auth is **disabled** — access control is at the APIM layer via subscription keys

## Tech Stack

- **API**: FastAPI (Python 3.11), SQLAlchemy 2.0 (async), Alembic migrations
- **Database**: PostgreSQL 16 (Azure Flexible Server in prod, Docker locally)
- **Infrastructure**: Azure Bicep, deployed via Azure Developer CLI (`azd`)
- **Hosting**: Azure Container Apps + Azure API Management (StandardV2)
- **CI/CD**: GitHub Actions

## Code Conventions

- SQLAlchemy 2.0 style (`mapped_column`, `Mapped` types)
- UUIDs as primary keys for all tables
- Pydantic v2 `model_config` style (no `class Config`)
- All API routes under `/api/v1/`
- Health checks at `/health` and `/health/db`
- Order number format: `ST-ORD-YYYYMM-NNNN`
- Async SQLAlchemy sessions throughout
- Service layer pattern: routers → services → database

## Local Development

```bash
# Start services
docker-compose up --build
# API docs at http://localhost:8000/docs

# Run tests
pip install -r requirements-dev.txt
pytest tests/ -v

# Lint
ruff check src/ tests/

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Environment Variables

- `DATABASE_URL` — PostgreSQL connection string (`postgresql+asyncpg://`). **Password must not contain `@`** — breaks URL parsing.
- `ENVIRONMENT` — dev/staging/production
- `LOG_LEVEL` — logging level (default: info)

## Azure Deployment

### Primary: Deploy with `azd`

```bash
azd init -e dev
azd env set PUBLISHER_EMAIL <email>
azd env set POSTGRES_ADMIN_PASSWORD <password-without-@>
azd up
```

`azd up` runs a two-phase deployment orchestrated by `azure.yaml`:
1. **Phase 1** — Provisions infrastructure via `infra/main.bicep` (using `main.bicepparam`) and builds/deploys the app container
2. **Phase 2** — The `postdeploy` hook (`hooks/postdeploy.sh` / `.ps1`) waits for health check, then re-runs Bicep with `DEPLOY_API_CONFIG=true` to import OpenAPI spec + configure MCP

Key environment variables (set via `azd env set`, read by `main.bicepparam`):
- `PUBLISHER_EMAIL` (required) — APIM publisher email
- `POSTGRES_ADMIN_PASSWORD` (required) — must not contain `@`
- `AUTH_CLIENT_ID` (optional) — Entra ID App Registration client ID
- `AI_FOUNDRY_PRINCIPAL_ID` (optional) — AI Foundry MI for APIM role assignment

### Secondary: GitHub Actions CI/CD

`.github/workflows/deploy.yml` runs on push to `main` with 4 jobs: deploy-infrastructure → build-and-push → deploy-app → configure-apim.

## Important Constraints

- PostgreSQL passwords must **not** contain `@` — breaks `postgresql+asyncpg://` connection strings
- APIM StandardV2 requires Bicep API version `2024-05-01` for child resources; MCP resources use `2025-03-01-preview`
- MCP API Bicep must set **both** `apiType: 'mcp'` and `type: 'mcp'` in properties
- Bicep `BCP037` warnings for MCP properties are expected and can be ignored
- APIM StandardV2 takes ~5 min to provision on first deployment

## Deployment Verification

After running `azd up` or a GitHub Actions deploy, verify success using these layered checks. Each layer depends on the previous one passing. Stop at the first failure and investigate.

### Step 0: Resolve Variables

All subsequent commands reference these variables. Resolve them first.

```bash
# Resource names (default environmentName = apim-mcp-dev)
RG="rg-poc-apim"
APP_NAME="apim-mcp-dev-app"
APIM_NAME="apim-mcp-dev-apim"
PG_NAME="apim-mcp-dev-pg"
ACR_NAME="apimmcpdevacr"

# Container App FQDN
APP_URL=$(az containerapp show \
  --resource-group $RG --name $APP_NAME \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# APIM gateway URL
APIM_URL=$(az apim show \
  --resource-group $RG --name $APIM_NAME \
  --query "gatewayUrl" -o tsv)

# Subscription key (via ARM listSecrets)
SUB_KEY=$(az rest --method post \
  --uri "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RG/providers/Microsoft.ApiManagement/service/$APIM_NAME/subscriptions/st-orders-free-subscription/listSecrets?api-version=2024-05-01" \
  --query "primaryKey" -o tsv)
```

### Layer 1: Quick Smoke Test

Verify the Container App is running and the database is connected. Source: `src/app/routers/health.py`.

```bash
# Health check — expect HTTP 200 with {"status": "healthy"}
curl -s "https://$APP_URL/health"

# Database check — expect {"status": "healthy", "database": "connected"}
curl -s "https://$APP_URL/health/db"
```

If health returns non-200, retry up to 10 times with 15-second intervals (mirrors `.github/workflows/deploy.yml` health check pattern):
```bash
for i in $(seq 1 10); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_URL/health" || true)
  if [ "$STATUS" = "200" ]; then echo "Healthy"; break; fi
  echo "Attempt $i/10 returned $STATUS. Retrying in 15s..."
  sleep 15
done
```

### Layer 2: Infrastructure Verification

Verify each Azure resource is in the expected state using `az` CLI.

```bash
# Container App — verify image is st-orders-api:<sha> (not the hello-world placeholder)
az containerapp show --resource-group $RG --name $APP_NAME \
  --query "properties.template.containers[0].image" -o tsv
# Expected: apimmcpdevacr.azurecr.io/st-orders-api:<git-sha>
# NOT: mcr.microsoft.com/azuredocs/containerapps-helloworld:latest

# APIM — verify provisioned with StandardV2 SKU
az apim show --resource-group $RG --name $APIM_NAME \
  --query "{state: provisioningState, sku: sku.name}" -o json
# Expected: {"state": "Succeeded", "sku": "StandardV2"}

# ACR — verify st-orders-api image exists with tags
az acr repository list --name $ACR_NAME -o json
# Expected: includes "st-orders-api"
az acr repository show-tags --name $ACR_NAME --repository st-orders-api -o json
# Expected: includes the deployed git SHA tag

# PostgreSQL — verify server is ready
az postgres flexible-server show --resource-group $RG --name $PG_NAME \
  --query "{state: state, version: version}" -o json
# Expected: {"state": "Ready", "version": "16"}

# APIM APIs — verify both REST API and MCP API exist
az apim api list --resource-group $RG --service-name $APIM_NAME \
  --query "[].{name: name, path: path}" -o table
# Expected: two rows:
#   st-orders-api   orders
#   st-orders-mcp   st-orders-mcp
```

### Layer 3: REST API Verification (through APIM)

Verify the REST API responds correctly through APIM with subscription key authentication.

```bash
# List products — expect 28 items from seed data
curl -s "$APIM_URL/orders/api/v1/products" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" | python -m json.tool | head -5

# List customers — expect 10 items
curl -s "$APIM_URL/orders/api/v1/customers" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" | python -m json.tool | head -5

# List orders — expect 40 items
curl -s "$APIM_URL/orders/api/v1/orders" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" | python -m json.tool | head -5

# Verify subscription key enforcement — unauthenticated request should return 401
curl -s -o /dev/null -w "%{http_code}" "$APIM_URL/orders/api/v1/products"
# Expected: 401
```

### Layer 4: MCP Verification (JSON-RPC through APIM)

Verify the APIM-native MCP server responds to JSON-RPC requests. Endpoint: `$APIM_URL/st-orders-mcp/mcp`.

```bash
MCP_ENDPOINT="$APIM_URL/st-orders-mcp/mcp"
MCP_HEADERS=(-H "Ocp-Apim-Subscription-Key: $SUB_KEY" \
             -H "Content-Type: application/json" \
             -H "Accept: application/json, text/event-stream")

# Initialize — expect result with serverInfo
curl -s -X POST "$MCP_ENDPOINT" "${MCP_HEADERS[@]}" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"verify","version":"1.0"}}}'
# Expected: JSON-RPC response with result.serverInfo

# List tools — expect exactly 8 tools
curl -s -X POST "$MCP_ENDPOINT" "${MCP_HEADERS[@]}" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'
# Expected 8 tool names (from infra/modules/apim-mcp.bicep lines 24-33):
#   list_products_api_v1_products_get
#   get_product_api_v1_products__product_id__get
#   list_customers_api_v1_customers_get
#   get_customer_api_v1_customers__customer_id__get
#   list_orders_api_v1_orders_get
#   get_order_api_v1_orders__order_id__get
#   create_order_api_v1_orders_post
#   update_order_api_v1_orders__order_id__put

# Call a tool — list products filtered by category
curl -s -X POST "$MCP_ENDPOINT" "${MCP_HEADERS[@]}" \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":3,"params":{"name":"list_products_api_v1_products_get","arguments":{"category":"Microcontrollers","limit":"2"}}}'
# Expected: JSON-RPC response with product data in result
```

### Layer 5: End-to-End Data Flow

Verify the full create-and-read cycle through the REST API. Schema reference: `src/app/schemas/order.py` — `OrderCreate` requires `customer_id` (UUID), `items` (list of `{product_id: UUID, quantity: int}`), and optionally `shipping_address` and `notes`.

```bash
# Get a customer ID from seed data
CUSTOMER_ID=$(curl -s "$APIM_URL/orders/api/v1/customers" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" \
  | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

# Get a product ID from seed data
PRODUCT_ID=$(curl -s "$APIM_URL/orders/api/v1/products" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" \
  | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

# Create an order — expect HTTP 201 with order_number format ST-ORD-YYYYMM-NNNN
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "$APIM_URL/orders/api/v1/orders" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\": \"$CUSTOMER_ID\", \"items\": [{\"product_id\": \"$PRODUCT_ID\", \"quantity\": 5}]}"
# Expected: HTTP 201, response contains order_number matching ST-ORD-YYYYMM-NNNN

# Verify the order appears in the pending orders list
curl -s "$APIM_URL/orders/api/v1/orders?status=pending" \
  -H "Ocp-Apim-Subscription-Key: $SUB_KEY" \
  | python -c "import sys,json; orders=json.load(sys.stdin); print(f'{len(orders)} pending orders found')"
# Expected: at least 1 pending order (the one just created)
```

## Project Structure

```
├── .github/workflows/    # CI (lint+test) and Deploy (4-phase pipeline)
├── hooks/                # azd lifecycle hooks (postdeploy = Phase 2 Bicep)
├── infra/                # Azure Bicep templates (main + 8 modules)
│   ├── main.bicep        # Orchestrator
│   ├── main.bicepparam   # Parameters (reads env vars via readEnvironmentVariable)
│   └── modules/
│       ├── managed-identity.bicep
│       ├── keyvault.bicep
│       ├── acr.bicep
│       ├── postgresql.bicep
│       ├── container-app.bicep
│       ├── apim.bicep
│       ├── apim-api.bicep      # REST API import + product + subscription
│       └── apim-mcp.bicep      # MCP server (routes through REST API)
├── src/app/              # FastAPI application
│   ├── main.py           # Entry point
│   ├── config.py         # pydantic-settings
│   ├── database.py       # SQLAlchemy engine/session
│   ├── models/           # customer, product, order, order_item
│   ├── schemas/          # Pydantic schemas per entity
│   ├── routers/          # health, customers, products, orders
│   ├── services/         # Business logic per entity
│   └── seed.py           # Seed data
├── alembic/              # Database migrations
├── tests/                # Pytest test suite
├── azure.yaml            # Azure Developer CLI project config
├── Dockerfile            # Multi-stage Python 3.11-slim
└── docker-compose.yml    # Local dev (PostgreSQL + app)
```
