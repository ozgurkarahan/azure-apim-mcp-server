// ============================================================================
// Main Orchestrator - Azure APIM MCP Server Infrastructure
// ============================================================================

targetScope = 'resourceGroup'

// --------------------------------------------------------------------------
// Parameters
// --------------------------------------------------------------------------

@description('Base environment name used as a prefix for all resources.')
param environmentName string = 'apim-mcp-dev'

@description('Azure region for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Publisher email address for the API Management instance.')
param publisherEmail string

@description('Publisher display name for the API Management instance.')
param publisherName string = 'Microelectronics Orders'

@description('Administrator password for the PostgreSQL server.')
@secure()
param postgresAdminPassword string

@description('Container image to deploy. Use a placeholder for initial deployment.')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Client ID of the Entra ID App Registration for Easy Auth (from az ad app create).')
param authClientId string

@description('Principal ID of the AI Foundry hub managed identity (for APIM role assignment). Leave empty to skip.')
param aiFoundryPrincipalId string = ''

// --------------------------------------------------------------------------
// Variables
// --------------------------------------------------------------------------

// ACR names must be alphanumeric (no hyphens), 5-50 characters
var acrName = replace('${environmentName}acr', '-', '')

// --------------------------------------------------------------------------
// Module: Managed Identity
// --------------------------------------------------------------------------
module identity 'modules/managed-identity.bicep' = {
  name: 'managed-identity'
  params: {
    name: '${environmentName}-identity'
    location: location
  }
}

// --------------------------------------------------------------------------
// Module: Key Vault
// --------------------------------------------------------------------------
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: '${environmentName}-kv'
    location: location
    principalId: identity.outputs.principalId
    postgresAdminPassword: postgresAdminPassword
  }
}

// --------------------------------------------------------------------------
// Module: Azure Container Registry
// --------------------------------------------------------------------------
module acr 'modules/acr.bicep' = {
  name: 'container-registry'
  params: {
    name: acrName
    location: location
    principalId: identity.outputs.principalId
  }
}

// --------------------------------------------------------------------------
// Module: PostgreSQL Flexible Server
// --------------------------------------------------------------------------
module postgres 'modules/postgresql.bicep' = {
  name: 'postgresql'
  params: {
    name: '${environmentName}-pg'
    location: location
    adminPassword: postgresAdminPassword
  }
}

// --------------------------------------------------------------------------
// Module: Container Apps
// --------------------------------------------------------------------------
var databaseUrl = 'postgresql+asyncpg://pgadmin:${postgresAdminPassword}@${postgres.outputs.fqdn}:5432/${postgres.outputs.databaseName}?ssl=require'

module containerApp 'modules/container-app.bicep' = {
  name: 'container-app'
  params: {
    name: '${environmentName}-app'
    location: location
    containerImage: containerImage
    managedIdentityId: identity.outputs.id
    acrLoginServer: acr.outputs.loginServer
    databaseUrl: databaseUrl
    authClientId: authClientId
    apimPrincipalId: apim.outputs.principalId
  }
}

// --------------------------------------------------------------------------
// Module: API Management
// --------------------------------------------------------------------------
module apim 'modules/apim.bicep' = {
  name: 'api-management'
  params: {
    name: '${environmentName}-apim'
    location: location
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// --------------------------------------------------------------------------
// Module: APIM API Configuration
// --------------------------------------------------------------------------
module apimApi 'modules/apim-api.bicep' = {
  name: 'apim-api'
  params: {
    apimName: apim.outputs.name
    apiBackendUrl: containerApp.outputs.url
    authAudience: 'api://${authClientId}'
  }
}

// --------------------------------------------------------------------------
// Module: APIM Native MCP Server
// --------------------------------------------------------------------------
module apimMcp 'modules/apim-mcp.bicep' = {
  name: 'apim-mcp'
  params: {
    apimName: apim.outputs.name
    apimGatewayUrl: apim.outputs.gatewayUrl
  }
  dependsOn: [
    apimApi
  ]
}

// --------------------------------------------------------------------------
// Module: APIM AI Foundry Role Assignments (conditional)
// --------------------------------------------------------------------------
module apimFoundryRoles 'modules/apim-foundry-roles.bicep' = if (!empty(aiFoundryPrincipalId)) {
  name: 'apim-foundry-roles'
  params: {
    apimName: apim.outputs.name
    aiFoundryPrincipalId: aiFoundryPrincipalId
  }
}

// --------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------

@description('Full URL of the deployed Container App.')
output containerAppUrl string = containerApp.outputs.url

@description('Gateway URL of the API Management instance.')
output apimGatewayUrl string = apim.outputs.gatewayUrl

@description('Login server URL for the Azure Container Registry.')
output acrLoginServer string = acr.outputs.loginServer

@description('Resource ID of the API Management instance.')
output apimResourceId string = apim.outputs.id

@description('MCP endpoint URL for AI assistant integrations.')
output mcpEndpoint string = apimMcp.outputs.mcpEndpoint
