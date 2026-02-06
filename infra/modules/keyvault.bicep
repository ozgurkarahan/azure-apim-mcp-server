// ============================================================================
// Module: Azure Key Vault
// ============================================================================

@description('Name of the Key Vault.')
param name string

@description('Azure region for the resource.')
param location string

@description('Principal ID to grant Key Vault access (Get, List secrets).')
param principalId string

@description('PostgreSQL administrator password to store as a secret.')
@secure()
param postgresAdminPassword string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enableRbacAuthorization: false
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

resource postgresPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-admin-password'
  properties: {
    value: postgresAdminPassword
  }
}

@description('Resource ID of the Key Vault.')
output id string = keyVault.id

@description('Name of the Key Vault.')
output name string = keyVault.name

@description('Secret URI for the PostgreSQL admin password.')
output secretUri string = postgresPasswordSecret.properties.secretUri
