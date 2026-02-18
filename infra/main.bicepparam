using './main.bicep'

// Environment name: sourced from azd env (AZURE_ENV_NAME), defaults to 'apim-mcp-dev' for manual deploys
param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'apim-mcp-dev')

// Required: publisher email for APIM instance
param publisherEmail = readEnvironmentVariable('PUBLISHER_EMAIL', '')

// Publisher display name for APIM
param publisherName = readEnvironmentVariable('PUBLISHER_NAME', 'Microelectronics Orders Admin')

// Required: PostgreSQL admin password. Must NOT contain '@' (breaks asyncpg connection string).
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD', '')

// Optional: Entra ID App Registration client ID for Easy Auth (disabled by default).
param authClientId = readEnvironmentVariable('AUTH_CLIENT_ID', '')

// Optional: AI Foundry hub managed identity principal ID for APIM role assignment.
param aiFoundryPrincipalId = readEnvironmentVariable('AI_FOUNDRY_PRINCIPAL_ID', '')

// Deploy APIM API import + MCP config. Set to false for Phase 1 (initial infra).
// azd uses Phase 1 (false) during provision, Phase 2 (true) via postdeploy hook.
param deployApiConfig = false
