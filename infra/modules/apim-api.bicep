// ============================================================================
// Module: APIM API Import, Product, Subscription, and Policies
// ============================================================================

@description('Name of the existing API Management instance.')
param apimName string

@description('Backend URL of the Container App (e.g., https://myapp.azurecontainerapps.io).')
param apiBackendUrl string

// --------------------------------------------------------------------------
// Reference existing APIM instance
// --------------------------------------------------------------------------
resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimName
}

// --------------------------------------------------------------------------
// Import API from OpenAPI specification
// --------------------------------------------------------------------------
resource api 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apim
  name: 'st-orders-api'
  properties: {
    displayName: 'ST Orders API'
    description: 'ST Micro Orders API imported from OpenAPI specification.'
    path: 'orders'
    protocols: [
      'https'
    ]
    format: 'openapi+json-link'
    value: '${apiBackendUrl}/openapi.json'
    serviceUrl: apiBackendUrl
    subscriptionRequired: true
  }
}

// --------------------------------------------------------------------------
// CORS Policy (allow Developer Portal)
// --------------------------------------------------------------------------
var corsPolicyXml = '<policies><inbound><base /><cors allow-credentials="true"><allowed-origins><origin>https://${apimName}.developer.azure-api.net</origin></allowed-origins><allowed-methods preflight-result-max-age="300"><method>GET</method><method>POST</method><method>PUT</method><method>DELETE</method><method>PATCH</method><method>OPTIONS</method></allowed-methods><allowed-headers><header>*</header></allowed-headers></cors></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'

resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'xml'
    value: corsPolicyXml
  }
}

// --------------------------------------------------------------------------
// Product: ST Orders API - Free (with rate limit)
// --------------------------------------------------------------------------
resource product 'Microsoft.ApiManagement/service/products@2023-09-01-preview' = {
  parent: apim
  name: 'st-orders-free'
  properties: {
    displayName: 'ST Orders API - Free'
    description: 'Free tier for the ST Orders API with rate limiting.'
    subscriptionRequired: true
    approvalRequired: false
    state: 'published'
  }
}

// Link the API to the product
resource productApi 'Microsoft.ApiManagement/service/products/apis@2023-09-01-preview' = {
  parent: product
  name: api.name
}

// Rate limit policy on the product (100 calls per minute)
resource productPolicy 'Microsoft.ApiManagement/service/products/policies@2023-09-01-preview' = {
  parent: product
  name: 'policy'
  properties: {
    format: 'xml'
    value: '''
<policies>
  <inbound>
    <base />
    <rate-limit calls="100" renewal-period="60" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>'''
  }
}

// --------------------------------------------------------------------------
// Subscription for the Free product
// --------------------------------------------------------------------------
resource subscription 'Microsoft.ApiManagement/service/subscriptions@2023-09-01-preview' = {
  parent: apim
  name: 'st-orders-free-subscription'
  properties: {
    displayName: 'ST Orders Free Subscription'
    scope: product.id
    state: 'active'
  }
}

@description('Resource ID of the imported API.')
output apiId string = api.id
