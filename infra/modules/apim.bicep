// ============================================================================
// Module: Azure API Management (Developer Tier)
// ============================================================================

@description('Name of the API Management instance.')
param name string

@description('Azure region for the resource.')
param location string

@description('Publisher email address for the APIM instance.')
param publisherEmail string

@description('Publisher display name for the APIM instance.')
param publisherName string

resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'Developer'
    capacity: 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

@description('Resource ID of the API Management instance.')
output id string = apim.id

@description('Name of the API Management instance.')
output name string = apim.name

@description('Gateway URL of the API Management instance.')
output gatewayUrl string = apim.properties.gatewayUrl

@description('Principal ID of the API Management system-assigned managed identity.')
output principalId string = apim.identity.principalId
