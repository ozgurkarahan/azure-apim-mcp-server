# =============================================================================
# Post-deploy hook: Phase 2 Bicep deployment (PowerShell)
# Waits for the Container App to be healthy, then deploys APIM API import
# and MCP configuration (deployApiConfig=true).
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "=== Post-deploy: Phase 2 (APIM API import + MCP config) ==="

# Determine the app URL from azd outputs
$AppUrl = if ($env:SERVICE_API_URI) { $env:SERVICE_API_URI } else { $env:CONTAINER_APP_URL }

if (-not $AppUrl) {
    Write-Error "Neither SERVICE_API_URI nor CONTAINER_APP_URL is set. Cannot determine Container App URL for health check."
    exit 1
}

$AppUrl = $AppUrl.TrimEnd('/')
$HealthUrl = "$AppUrl/health"

Write-Host "Health check endpoint: $HealthUrl"

# Wait for the app to become healthy (max 5 minutes)
$MaxAttempts = 30
$SleepSeconds = 10

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-Host "Health check attempt $attempt/$MaxAttempts..."

    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
        $statusCode = $response.StatusCode
    } catch {
        $statusCode = 0
    }

    if ($statusCode -eq 200) {
        Write-Host "App is healthy (HTTP 200)."
        break
    }

    if ($attempt -eq $MaxAttempts) {
        Write-Error "App did not become healthy after $MaxAttempts attempts. Last status code: $statusCode"
        exit 1
    }

    Write-Host "  Status: $statusCode - retrying in ${SleepSeconds}s..."
    Start-Sleep -Seconds $SleepSeconds
}

# Run Phase 2 Bicep deployment with deployApiConfig=true
Write-Host ""
Write-Host "Deploying Phase 2 Bicep (deployApiConfig=true)..."

$ResourceGroup = if ($env:AZURE_RESOURCE_GROUP) { $env:AZURE_RESOURCE_GROUP } else { "rg-$env:AZURE_ENV_NAME" }
$PublisherName = if ($env:PUBLISHER_NAME) { $env:PUBLISHER_NAME } else { "Microelectronics Orders" }
$AuthClientId = if ($env:AUTH_CLIENT_ID) { $env:AUTH_CLIENT_ID } else { "" }
$AiFoundryPrincipalId = if ($env:AI_FOUNDRY_PRINCIPAL_ID) { $env:AI_FOUNDRY_PRINCIPAL_ID } else { "" }
$deploymentName = "phase2-$(Get-Date -Format 'yyyyMMddHHmmss')"

az deployment group create `
    --resource-group $ResourceGroup `
    --template-file ./infra/main.bicep `
    --parameters `
        environmentName="$env:AZURE_ENV_NAME" `
        location="$env:AZURE_LOCATION" `
        publisherEmail="$env:PUBLISHER_EMAIL" `
        publisherName="$PublisherName" `
        postgresAdminPassword="$env:POSTGRES_ADMIN_PASSWORD" `
        authClientId="$AuthClientId" `
        aiFoundryPrincipalId="$AiFoundryPrincipalId" `
        deployApiConfig=true `
    --name $deploymentName `
    --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase 2 Bicep deployment failed."
    exit 1
}

Write-Host ""
Write-Host "=== Phase 2 deployment complete ==="
Write-Host "APIM API import and MCP configuration deployed successfully."
