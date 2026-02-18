# Architecture - Microelectronics Orders API

Azure-based platform for managing semiconductor orders, exposed via REST API and native MCP server through Azure API Management.

## Azure Resources

**Resource Group:** `rg-poc-apim` | **Region:** `swedencentral`

| # | Resource | Azure Type | SKU/Tier | Name |
|---|----------|-----------|----------|------|
| 1 | Managed Identity | `Microsoft.ManagedIdentity/userAssignedIdentities` | - | `apim-mcp-dev-identity` |
| 2 | Key Vault | `Microsoft.KeyVault/vaults` | Standard | `apim-mcp-dev-kv` |
| 3 | Container Registry | `Microsoft.ContainerRegistry/registries` | Basic | `apimmcpdevacr` |
| 4 | PostgreSQL Flexible Server | `Microsoft.DBforPostgreSQL/flexibleServers` | Burstable B1ms | `apim-mcp-dev-pg` |
| 5 | PostgreSQL Database | (sub-resource of #4) | PostgreSQL 16 | `storders` |
| 6 | Log Analytics Workspace | `Microsoft.OperationalInsights/workspaces` | PerGB2018 | `apim-mcp-dev-app-logs` |
| 7 | Container Apps Environment | `Microsoft.App/managedEnvironments` | - | `apim-mcp-dev-app-env` |
| 8 | Container App | `Microsoft.App/containerApps` | 0.5 CPU, 1GB RAM, 1-3 replicas | `apim-mcp-dev-app` |
| 9 | API Management | `Microsoft.ApiManagement/service` | StandardV2 | `apim-mcp-dev-apim` |
| 10 | APIM REST API | `Microsoft.ApiManagement/service/apis` | - | `st-orders-api` |
| 11 | APIM MCP API | `Microsoft.ApiManagement/service/apis` (preview) | apiType: mcp | `st-orders-mcp` |
| 12 | APIM Product | `Microsoft.ApiManagement/service/products` | - | `st-orders-free` |
| 13 | APIM Subscription | `Microsoft.ApiManagement/service/subscriptions` | - | `st-orders-free-subscription` |

## High-Level Overview

![High-Level Overview](overview.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph LR
    subgraph "Clients"
        REST_CLIENT["REST Client"]
        MCP_CLIENT["AI Assistant<br/>(MCP)"]
    end

    APIM["API Management<br/>(StandardV2)"]

    subgraph "Backend"
        APP["Container App<br/>(FastAPI)"]
        PG[("PostgreSQL")]
    end

    SECRETS["Identity<br/>& Secrets"]

    subgraph "CI/CD"
        GH["GitHub Actions"]
        ACR["Container<br/>Registry"]
    end

    REST_CLIENT -->|"subscription key"| APIM
    MCP_CLIENT -->|"subscription key"| APIM
    APIM --> APP
    APP --> PG
    APP -.->|"MI + Key Vault"| SECRETS
    GH -->|"docker push"| ACR
    ACR -->|"image pull"| APP
    GH -->|"Bicep deploy"| APP
```

</details>

## API Management

![API Management Detail](detail-apim.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph TB
    subgraph "Clients"
        DEV["Developer / Client App"]
        AI["AI Assistant<br/>(Claude, Copilot...)"]
    end

    subgraph "API Management — apim-mcp-dev-apim (StandardV2)"
        GW["Gateway<br/>*.azure-api.net"]
        REST["REST API<br/>st-orders-api<br/>/orders/api/v1/*"]
        MCP["MCP Server (native)<br/>st-orders-mcp<br/>/st-orders-mcp/mcp"]
        PROD["Product: st-orders-free<br/>Rate limit: 100 req/min"]
        SUB["Subscription Key"]
        NV["Named Value<br/>st-orders-internal-key"]
    end

    BACKEND["Container App<br/>(backend)"]

    DEV -->|"REST + Sub Key"| GW
    AI -->|"MCP + Sub Key"| GW
    GW --> REST
    GW --> MCP
    MCP -->|"internal sub key<br/>(set-header policy)"| REST
    REST --> PROD
    PROD --> SUB
    NV -.->|"injected by policy"| MCP
    GW -->|"forward request"| BACKEND
```

</details>

## Authentication Flow

![Authentication Flow](detail-auth.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
sequenceDiagram
    participant Client
    participant APIM as APIM (StandardV2)
    participant App as Container App

    Note over Client,App: REST API Flow
    Client->>APIM: Request + Subscription Key
    APIM->>APIM: Validate subscription key
    APIM->>App: Forward request
    App->>App: Process request
    App-->>Client: Response (via APIM)

    Note over Client,App: MCP Flow
    Client->>APIM: JSON-RPC tool call + Subscription Key
    APIM->>APIM: Validate subscription key
    APIM->>APIM: Translate tool call → REST operation
    APIM->>APIM: Inject internal subscription key (set-header)
    APIM->>APIM: Route to APIM REST API
    APIM->>App: Forward REST request
    App-->>Client: Response → JSON-RPC result (via APIM)
```

</details>

## Container Apps & Data

![Container Apps & Data](detail-app.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph TB
    subgraph "Container Apps Environment — apim-mcp-dev-app-env"
        APP["Container App<br/>apim-mcp-dev-app<br/>FastAPI (Python 3.11)<br/>Port 8000 | 0.5 CPU, 1GB RAM<br/>1–3 replicas"]
    end

    LOGS["Log Analytics Workspace<br/>apim-mcp-dev-app-logs<br/>(PerGB2018)"]

    subgraph "Data"
        PG["PostgreSQL Flexible Server<br/>apim-mcp-dev-pg<br/>v16 — Burstable B1ms, 32GB<br/>DB: storders"]
    end

    APIM["API Management<br/>(StandardV2)"]

    APIM -->|"forward request"| APP
    APP -->|"asyncpg"| PG
    APP -->|"logs & metrics"| LOGS
```

</details>

## Identity & Secrets

![Identity & Secrets](detail-identity.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph TB
    subgraph "User-Assigned Managed Identity — apim-mcp-dev-identity"
        UA_MI["User-Assigned MI"]
    end

    APP["Container App<br/>apim-mcp-dev-app"]
    ACR["Container Registry<br/>apimmcpdevacr"]
    KV["Key Vault<br/>apim-mcp-dev-kv<br/>Secret: postgres-admin-password"]
    APIM["API Management<br/>apim-mcp-dev-apim<br/>(System-Assigned MI)"]
    FOUNDRY["AI Foundry MI<br/>(conditional role assignment)"]

    APP -.->|"uses identity"| UA_MI
    UA_MI -->|"AcrPull role"| ACR
    UA_MI -->|"get / list secrets"| KV
    FOUNDRY -->|"API Management<br/>Service Contributor"| APIM
```

</details>

## Deployment with `azd`

The primary deployment method uses the [Azure Developer CLI (`azd`)](https://learn.microsoft.com/azure/developer/azure-developer-cli/). The project is configured via `azure.yaml` with a two-phase Bicep deployment orchestrated by a postdeploy hook.

![Deployment with azd](detail-azd.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph LR
    DEV["Developer"]

    subgraph "azd up"
        PROVISION["Phase 1<br/>Provision Infrastructure<br/>(main.bicep via main.bicepparam)"]
        DEPLOY_APP["Build & Deploy<br/>Container App"]
        HOOK["postdeploy hook<br/>(hooks/postdeploy.sh)"]
    end

    AZURE["Azure Resources<br/>(ACR, APIM, PostgreSQL,<br/>Container App)"]
    HEALTH["Health Check<br/>/health → 200"]
    PHASE2["Phase 2 Bicep<br/>DEPLOY_API_CONFIG=true<br/>(API import + MCP config)"]

    DEV -->|"azd up"| PROVISION
    PROVISION -->|"Bicep deploy"| AZURE
    PROVISION --> DEPLOY_APP
    DEPLOY_APP -->|"docker build + push"| AZURE
    DEPLOY_APP --> HOOK
    HOOK --> HEALTH
    HEALTH --> PHASE2
    PHASE2 -->|"OpenAPI import +<br/>MCP tools"| AZURE
```

</details>

**Key files:**
- `azure.yaml` — project configuration (services, hooks)
- `infra/main.bicepparam` — parameters read from environment variables (set via `azd env set`)
- `hooks/postdeploy.sh` / `postdeploy.ps1` — waits for health, runs Phase 2 Bicep

## CI/CD Pipeline (GitHub Actions)

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automates the same two-phase deployment on push to `main`.

![CI/CD Pipeline](detail-cicd.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph LR
    GH["GitHub<br/>(push to main)"]

    subgraph "GitHub Actions Pipeline"
        INFRA["Job 1<br/>deploy-infrastructure<br/>(Phase 1 Bicep)"]
        BUILD["Job 2<br/>build-and-push<br/>(Docker → ACR)"]
        DEPLOY["Job 3<br/>deploy-app<br/>(update container image)"]
        CONFIG["Job 4<br/>configure-apim<br/>(health check + Phase 2 Bicep)"]
    end

    ACR["ACR<br/>apimmcpdevacr"]
    AZURE["Azure Resources<br/>(Bicep)"]
    APP["Container App<br/>apim-mcp-dev-app"]
    APIM["APIM<br/>apim-mcp-dev-apim"]

    GH --> INFRA
    INFRA -->|"az deployment group create<br/>infra/main.bicepparam"| AZURE
    INFRA --> BUILD
    BUILD -->|"docker push<br/>st-orders-api:sha"| ACR
    BUILD --> DEPLOY
    DEPLOY -->|"az containerapp update"| APP
    DEPLOY --> CONFIG
    CONFIG -->|"Phase 2 Bicep<br/>DEPLOY_API_CONFIG=true"| APIM
```

</details>

## MCP Tools

8 tools exposed via the native APIM MCP server (`st-orders-mcp`), each mapped to a REST API operation:

| Tool | REST Operation |
|------|---------------|
| `list_products_api_v1_products_get` | GET /api/v1/products |
| `get_product_api_v1_products__product_id__get` | GET /api/v1/products/{id} |
| `list_customers_api_v1_customers_get` | GET /api/v1/customers |
| `get_customer_api_v1_customers__customer_id__get` | GET /api/v1/customers/{id} |
| `list_orders_api_v1_orders_get` | GET /api/v1/orders |
| `get_order_api_v1_orders__order_id__get` | GET /api/v1/orders/{id} |
| `create_order_api_v1_orders_post` | POST /api/v1/orders |
| `update_order_api_v1_orders__order_id__put` | PUT /api/v1/orders/{id} |

**MCP Endpoint:** `https://apim-mcp-dev-apim.azure-api.net/st-orders-mcp/mcp`

## Bicep Modules

Infrastructure-as-Code is organized in `infra/`:

```
infra/
  main.bicep                    # Orchestrator
  main.bicepparam               # Parameters (reads env vars from azd)
  modules/
    managed-identity.bicep      # User-assigned MI
    keyvault.bicep              # Key Vault + secrets
    acr.bicep                   # Container Registry + AcrPull role
    postgresql.bicep            # PostgreSQL + database
    container-app.bicep         # Environment + App
    apim.bicep                  # API Management instance
    apim-api.bicep              # REST API definition
    apim-mcp.bicep              # MCP Server API (preview)
    apim-foundry-roles.bicep    # AI Foundry role assignments (conditional)
```
