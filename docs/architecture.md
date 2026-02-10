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
| 9 | Easy Auth (Entra ID) | `Microsoft.App/containerApps/authConfigs` | - | (on Container App) |
| 10 | API Management | `Microsoft.ApiManagement/service` | Developer | `apim-mcp-dev-apim` |
| 11 | APIM REST API | `Microsoft.ApiManagement/service/apis` | - | `st-orders-api` |
| 12 | APIM MCP API | `Microsoft.ApiManagement/service/apis` (preview) | apiType: mcp | `st-orders-mcp` |
| 13 | APIM Product | `Microsoft.ApiManagement/service/products` | - | `st-orders-free` |
| 14 | APIM Subscription | `Microsoft.ApiManagement/service/subscriptions` | - | `st-orders-free-subscription` |

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

    APIM["API Management"]

    subgraph "Backend"
        APP["Container App<br/>(FastAPI)"]
        PG[("PostgreSQL")]
    end

    AUTH["Entra ID<br/>+ Easy Auth"]
    SECRETS["Identity<br/>& Secrets"]

    subgraph "CI/CD"
        GH["GitHub Actions"]
        ACR["Container<br/>Registry"]
    end

    REST_CLIENT -->|"subscription key"| APIM
    MCP_CLIENT -->|"subscription key"| APIM
    APIM -->|"Bearer token"| APP
    APP --> PG
    APIM <-.->|"token via MI"| AUTH
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

    subgraph "API Management — apim-mcp-dev-apim (Developer tier)"
        GW["Gateway<br/>*.azure-api.net"]
        REST["REST API<br/>st-orders-api<br/>/orders/api/v1/*"]
        MCP["MCP Server (native)<br/>st-orders-mcp<br/>/st-orders-mcp/mcp"]
        PROD["Product: st-orders-free<br/>Rate limit: 100 req/min"]
        SUB["Subscription Key"]
        MI["System-Assigned<br/>Managed Identity"]
    end

    BACKEND["Container App<br/>(backend)"]
    ENTRA["Entra ID<br/>(token endpoint)"]

    DEV -->|"REST + Sub Key"| GW
    AI -->|"MCP + Sub Key"| GW
    GW --> REST
    GW --> MCP
    REST --> PROD
    MCP --> PROD
    PROD --> SUB
    MI -->|"acquire token<br/>audience: api://8b7ac3cc-..."| ENTRA
    GW -->|"forward + Bearer token"| BACKEND
```

</details>

## Authentication Flow

![Authentication Flow](detail-auth.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
sequenceDiagram
    participant Client
    participant APIM
    participant EntraID as Entra ID
    participant EasyAuth as Easy Auth
    participant App as Container App

    Client->>APIM: Request + Subscription Key
    APIM->>EntraID: Acquire token (MI)<br/>audience: api://8b7ac3cc-...
    EntraID-->>APIM: Bearer Token (v1)
    APIM->>EasyAuth: Forward request + Bearer Token
    EasyAuth->>EasyAuth: Validate issuer, audience, principal
    EasyAuth->>App: Authenticated request
    App->>App: Process request
    App-->>Client: Response (via APIM)
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
        AUTH["Easy Auth<br/>(Entra ID validation)"]
    end

    LOGS["Log Analytics Workspace<br/>apim-mcp-dev-app-logs<br/>(PerGB2018)"]

    subgraph "Data"
        PG["PostgreSQL Flexible Server<br/>apim-mcp-dev-pg<br/>v16 — Burstable B1ms, 32GB<br/>DB: storders"]
    end

    APIM["API Management<br/>(inbound)"]

    APIM -->|"Bearer token"| AUTH
    AUTH -->|"validated request"| APP
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

    subgraph "APIM System-Assigned MI"
        SYS_MI["System MI<br/>(apim-mcp-dev-apim)"]
    end

    APP["Container App<br/>apim-mcp-dev-app"]
    ACR["Container Registry<br/>apimmcpdevacr"]
    KV["Key Vault<br/>apim-mcp-dev-kv<br/>Secret: postgres-admin-password"]
    ENTRA["Entra ID<br/>App Registration<br/>api://8b7ac3cc-..."]

    APP -.->|"uses identity"| UA_MI
    UA_MI -->|"AcrPull role"| ACR
    UA_MI -->|"get / list secrets"| KV
    SYS_MI -->|"acquire token<br/>audience: api://8b7ac3cc-..."| ENTRA
```

</details>

## CI/CD Pipeline

![CI/CD Pipeline](detail-cicd.png)

<details>
<summary>Mermaid source (click to expand)</summary>

```mermaid
graph LR
    GH["GitHub<br/>(push to main)"]

    subgraph "GitHub Actions Pipeline"
        BUILD["Job 1<br/>Build & Push"]
        INFRA["Job 2<br/>Deploy Infrastructure"]
        DEPLOY["Job 3<br/>Deploy App"]
        CONFIG["Job 4<br/>Configure APIM"]
    end

    ACR["ACR<br/>apimmcpdevacr"]
    AZURE["Azure Resources<br/>(Bicep)"]
    APP["Container App<br/>apim-mcp-dev-app"]
    APIM["APIM<br/>apim-mcp-dev-apim"]

    GH --> BUILD
    BUILD -->|"docker push<br/>st-orders-api:latest"| ACR
    BUILD --> INFRA
    INFRA -->|"az deployment group create<br/>infra/main.bicep"| AZURE
    INFRA --> DEPLOY
    DEPLOY -->|"update container image"| APP
    DEPLOY --> CONFIG
    CONFIG -->|"import openapi.json"| APIM
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
  modules/
    managed-identity.bicep      # User-assigned MI
    keyvault.bicep              # Key Vault + secrets
    acr.bicep                   # Container Registry + AcrPull role
    postgresql.bicep            # PostgreSQL + database
    container-app.bicep         # Environment + App + Easy Auth
    apim.bicep                  # API Management instance
    apim-api.bicep              # REST API definition
    apim-mcp.bicep              # MCP Server API (preview)
```
