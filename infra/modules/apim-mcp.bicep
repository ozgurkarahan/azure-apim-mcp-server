// ============================================================================
// Module: APIM Native MCP Server
// Exposes the ST Orders REST API as an MCP server using APIM's native MCP feature.
// APIM converts existing REST API operations into MCP tools automatically.
//
// Requires API version 2025-03-01-preview. Bicep will show schema warnings
// for MCP-specific properties (apiType, type, mcpTools) because the types
// aren't in the published Bicep schema yet — deploys successfully regardless.
// ============================================================================

@description('Name of the existing API Management instance.')
param apimName string

@description('Entra ID audience URI for managed identity authentication (e.g., api://<clientId>).')
param authAudience string

// --------------------------------------------------------------------------
// Operations to expose as MCP tools
// --------------------------------------------------------------------------
var mcpOperations = [
  'list_products_api_v1_products_get'
  'get_product_api_v1_products__product_id__get'
  'list_customers_api_v1_customers_get'
  'get_customer_api_v1_customers__customer_id__get'
  'list_orders_api_v1_orders_get'
  'get_order_api_v1_orders__order_id__get'
  'create_order_api_v1_orders_post'
  'update_order_api_v1_orders__order_id__put'
]

// --------------------------------------------------------------------------
// Reference existing APIM instance, REST API, and operations
// --------------------------------------------------------------------------
resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' existing = {
  name: apimName
}

resource restApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' existing = {
  parent: apim
  name: 'st-orders-api'
}

resource operations 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' existing = [for op in mcpOperations: {
  parent: restApi
  name: op
}]

// --------------------------------------------------------------------------
// MCP API Resource
// --------------------------------------------------------------------------
resource mcpApi 'Microsoft.ApiManagement/service/apis@2025-03-01-preview' = {
  parent: apim
  name: 'st-orders-mcp'
  properties: {
    displayName: 'ST Orders MCP Server'
    description: 'MCP server that exposes ST Orders API operations as tools for AI assistants.'
    path: 'st-orders-mcp'
    protocols: [
      'https'
    ]
    subscriptionRequired: true
    apiType: 'mcp'
    type: 'mcp'
    mcpTools: [for (op, i) in mcpOperations: {
      name: operations[i].name
      operationId: operations[i].id
    }]
  }
}

// --------------------------------------------------------------------------
// Inbound Policy: Managed Identity Authentication
// Same auth as the REST API — APIM acquires Entra ID token via its
// system-assigned MI to authenticate to the Container App backend.
// --------------------------------------------------------------------------
var mcpPolicyXml = '<policies><inbound><base /><authentication-managed-identity resource="${authAudience}" /></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'

resource mcpApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2025-03-01-preview' = {
  parent: mcpApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: mcpPolicyXml
  }
}

// --------------------------------------------------------------------------
// Link MCP API to the existing "ST Orders Free" product
// so the same subscription key works for both REST and MCP.
// --------------------------------------------------------------------------
resource product 'Microsoft.ApiManagement/service/products@2023-09-01-preview' existing = {
  parent: apim
  name: 'st-orders-free'
}

resource mcpProductApi 'Microsoft.ApiManagement/service/products/apis@2023-09-01-preview' = {
  parent: product
  name: mcpApi.name
}

// --------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------
@description('MCP endpoint URL.')
output mcpEndpoint string = '${apim.properties.gatewayUrl}/st-orders-mcp/mcp'
