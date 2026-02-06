// ============================================================================
// Module: Azure Container Registry
// ============================================================================

@description('Name of the Container Registry. Must be globally unique and alphanumeric.')
param name string

@description('Azure region for the resource.')
param location string

@description('Principal ID to assign the AcrPull role.')
param principalId string

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

// AcrPull built-in role definition ID
var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, principalId, acrPullRoleDefinitionId)
  scope: containerRegistry
  properties: {
    principalId: principalId
    roleDefinitionId: acrPullRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

@description('Name of the Container Registry.')
output name string = containerRegistry.name

@description('Login server URL for the Container Registry.')
output loginServer string = containerRegistry.properties.loginServer
