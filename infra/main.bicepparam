using './main.bicep'

param environmentName = 'apim-mcp-dev'

// TODO: Replace with a valid email address before deployment
param publisherEmail = 'admin@example.com'

param publisherName = 'Microelectronics Orders Admin'

// TODO: Replace with a strong password before deployment. Consider using Azure Key Vault references in CI/CD.
param postgresAdminPassword = 'REPLACE_WITH_SECURE_PASSWORD'
