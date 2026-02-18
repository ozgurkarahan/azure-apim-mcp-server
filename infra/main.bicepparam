using './main.bicep'

param environmentName = 'apim-mcp-dev'

// Required: Replace with your email address
param publisherEmail = '<your-email@example.com>'

param publisherName = 'Microelectronics Orders Admin'

// Required: Generate a strong password. Must NOT contain '@' (breaks asyncpg connection string).
param postgresAdminPassword = '<generate-a-strong-password-without-@>'

// Optional: Entra ID App Registration client ID for Easy Auth (disabled by default).
// Uncomment to enable auth config on the Container App.
// param authClientId = '<entra-app-client-id>'

// Optional: AI Foundry hub managed identity principal ID for APIM role assignment.
// Uncomment to deploy Foundry role assignments.
// param aiFoundryPrincipalId = '<foundry-mi-principal-id>'

// Optional: Set to false for initial deployment (before app is healthy).
// The deploy workflow handles this automatically via two-phase deployment.
// param deployApiConfig = true
