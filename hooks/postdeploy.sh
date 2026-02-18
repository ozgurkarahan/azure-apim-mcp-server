#!/bin/sh
# =============================================================================
# Post-deploy hook: Phase 2 Bicep deployment
# Waits for the Container App to be healthy, then deploys APIM API import
# and MCP configuration (deployApiConfig=true).
# =============================================================================

set -e

echo "=== Post-deploy: Phase 2 (APIM API import + MCP config) ==="

# Determine the app URL from azd outputs
APP_URL="${SERVICE_API_URI:-$CONTAINER_APP_URL}"

if [ -z "$APP_URL" ]; then
  echo "ERROR: Neither SERVICE_API_URI nor CONTAINER_APP_URL is set."
  echo "Cannot determine Container App URL for health check."
  exit 1
fi

# Strip trailing slash
APP_URL="${APP_URL%/}"
HEALTH_URL="${APP_URL}/health"

echo "Health check endpoint: ${HEALTH_URL}"

# Wait for the app to become healthy (max 5 minutes)
MAX_ATTEMPTS=30
SLEEP_SECONDS=10
attempt=1

while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  echo "Health check attempt ${attempt}/${MAX_ATTEMPTS}..."

  status_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

  if [ "$status_code" = "200" ]; then
    echo "App is healthy (HTTP 200)."
    break
  fi

  if [ "$attempt" -eq "$MAX_ATTEMPTS" ]; then
    echo "ERROR: App did not become healthy after ${MAX_ATTEMPTS} attempts."
    echo "Last status code: ${status_code}"
    exit 1
  fi

  echo "  Status: ${status_code} — retrying in ${SLEEP_SECONDS}s..."
  sleep "$SLEEP_SECONDS"
  attempt=$((attempt + 1))
done

# Run Phase 2 Bicep deployment with deployApiConfig=true
# Uses main.bicepparam which reads all parameters from environment variables.
# azd exports all .env values as env vars for hooks, so AZURE_ENV_NAME,
# PUBLISHER_EMAIL, etc. are already available. We just set DEPLOY_API_CONFIG=true.
echo ""
echo "Deploying Phase 2 Bicep (deployApiConfig=true)..."

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-${AZURE_ENV_NAME}}"
export DEPLOY_API_CONFIG=true

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --parameters ./infra/main.bicepparam \
  --name "phase2-$(date +%Y%m%d%H%M%S)" \
  --verbose

echo ""
echo "=== Phase 2 deployment complete ==="
echo "APIM API import and MCP configuration deployed successfully."
