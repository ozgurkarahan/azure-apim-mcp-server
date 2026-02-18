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
# Uses main.bicepparam which reads all parameters from environment variables.
# azd exports all .env values as env vars for hooks, so AZURE_ENV_NAME,
# PUBLISHER_EMAIL, etc. are already available. We just set DEPLOY_API_CONFIG=true.
Write-Host ""
Write-Host "Deploying Phase 2 Bicep (deployApiConfig=true)..."

$ResourceGroup = if ($env:AZURE_RESOURCE_GROUP) { $env:AZURE_RESOURCE_GROUP } else { "rg-$env:AZURE_ENV_NAME" }
$env:DEPLOY_API_CONFIG = "true"
$deploymentName = "phase2-$(Get-Date -Format 'yyyyMMddHHmmss')"

az deployment group create `
    --resource-group $ResourceGroup `
    --parameters ./infra/main.bicepparam `
    --name $deploymentName `
    --verbose

if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase 2 Bicep deployment failed."
    exit 1
}

Write-Host ""
Write-Host "=== Phase 2 deployment complete ==="
Write-Host "APIM API import and MCP configuration deployed successfully."
