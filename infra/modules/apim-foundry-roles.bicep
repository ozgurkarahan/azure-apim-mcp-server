// ============================================================================
// Module: APIM Role Assignments for AI Foundry Integration
// ============================================================================
// Grants the AI Foundry hub's managed identity the API Management Service
// Contributor role on the APIM instance, enabling AI Gateway management.

@description('Name of the existing API Management instance.')
param apimName string

@description('Principal ID of the AI Foundry hub managed identity.')
param aiFoundryPrincipalId string

// Reference the existing APIM instance
resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimName
}

// Built-in role: API Management Service Contributor
// https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#api-management-service-contributor
var apiManagementContributorRoleId = '312a565d-c81f-4fd8-895a-4e21e48d571c'

resource foundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: apim
  name: guid(apim.id, aiFoundryPrincipalId, apiManagementContributorRoleId)
  properties: {
    principalId: aiFoundryPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', apiManagementContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}
