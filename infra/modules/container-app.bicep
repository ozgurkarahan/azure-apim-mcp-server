// ============================================================================
// Module: Azure Container Apps Environment + Container App
// ============================================================================

@description('Base name for the Container App and related resources.')
param name string

@description('Azure region for the resource.')
param location string

@description('Full container image reference (e.g., myacr.azurecr.io/myapp:latest).')
param containerImage string

@description('Resource ID of the user-assigned managed identity.')
param managedIdentityId string

@description('Login server URL of the Azure Container Registry.')
param acrLoginServer string

@description('PostgreSQL connection string.')
@secure()
param databaseUrl string

@description('Application environment name.')
param environment string = 'production'

@description('Client ID of the Entra ID App Registration for Easy Auth.')
param authClientId string

@description('Principal ID of the APIM system-assigned managed identity (allowed to call this app).')
param apimPrincipalId string

// --------------------------------------------------------------------------
// Log Analytics Workspace
// --------------------------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${name}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// --------------------------------------------------------------------------
// Container Apps Environment
// --------------------------------------------------------------------------
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${name}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// --------------------------------------------------------------------------
// Container App
// --------------------------------------------------------------------------
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      secrets: [
        {
          name: 'database-url'
          value: databaseUrl
        }
      ]
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'LOG_LEVEL'
              value: environment == 'production' ? 'info' : 'debug'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// --------------------------------------------------------------------------
// Easy Auth (Microsoft Entra ID)
// --------------------------------------------------------------------------
resource authConfig 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: containerApp
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'Return401'
      excludedPaths: [
        '/health'
        '/openapi.json'
      ]
    }
    identityProviders: {
      azureActiveDirectory: {
        registration: {
          clientId: authClientId
          openIdIssuer: 'https://sts.windows.net/${tenant().tenantId}/'
        }
        validation: {
          defaultAuthorizationPolicy: {
            allowedPrincipals: {
              identities: [
                apimPrincipalId
              ]
            }
          }
          allowedAudiences: [
            'api://${authClientId}'
            authClientId
          ]
        }
      }
    }
  }
}

@description('Fully qualified domain name of the Container App.')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Full URL of the Container App.')
output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
