// ============================================================================
// Module: User-Assigned Managed Identity
// ============================================================================

@description('Name of the user-assigned managed identity.')
param name string

@description('Azure region for the resource.')
param location string

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
}

@description('Resource ID of the managed identity.')
output id string = managedIdentity.id

@description('Principal (object) ID of the managed identity.')
output principalId string = managedIdentity.properties.principalId

@description('Client (application) ID of the managed identity.')
output clientId string = managedIdentity.properties.clientId
