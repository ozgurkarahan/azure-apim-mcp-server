// ============================================================================
// Module: APIM Native MCP Server
// Exposes the ST Orders REST API as an MCP server using APIM's native MCP feature.
// APIM converts existing REST API operations into MCP tools automatically.
//
// Routing: MCP tool calls route through the APIM REST API endpoint (/orders)
// via an internal subscription key (stored as named value), NOT directly to
// the Container App. The REST API handles managed identity auth to the backend.
//
// API versions: 2025-03-01-preview for MCP resources (apiType/mcpTools),
// 2024-05-01 for all other APIM child resources (required for StandardV2).
// Bicep shows BCP037 warnings for MCP properties — expected and safe to ignore.
// ============================================================================

@description('Name of the existing API Management instance.')
param apimName string

@description('Gateway URL of the API Management instance (e.g., https://apim-mcp-dev-apim.azure-api.net).')
param apimGatewayUrl string

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
resource apim 'Microsoft.ApiManagement/service@2024-05-01' existing = {
  name: apimName
}

resource restApi 'Microsoft.ApiManagement/service/apis@2024-05-01' existing = {
  parent: apim
  name: 'st-orders-api'
}

resource operations 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' existing = [for op in mcpOperations: {
  parent: restApi
  name: op
}]

// --------------------------------------------------------------------------
// Internal subscription key: stored as a named value so the MCP API
// can route calls through the APIM REST API endpoint (which handles
// managed identity auth to the Container App).
// --------------------------------------------------------------------------
resource existingSubscription 'Microsoft.ApiManagement/service/subscriptions@2024-05-01' existing = {
  parent: apim
  name: 'st-orders-free-subscription'
}

resource internalKeyNamedValue 'Microsoft.ApiManagement/service/namedValues@2024-05-01' = {
  parent: apim
  name: 'st-orders-internal-key'
  properties: {
    displayName: 'st-orders-internal-key'
    value: existingSubscription.listSecrets().primaryKey
    secret: true
  }
}

// --------------------------------------------------------------------------
// MCP API Resource
// Routes tool calls through the APIM REST API endpoint (/orders) instead
// of calling the Container App directly. The REST API handles backend
// authentication via managed identity.
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
    serviceUrl: '${apimGatewayUrl}/orders'
    mcpTools: [for (op, i) in mcpOperations: {
      name: operations[i].name
      operationId: operations[i].id
    }]
  }
}

// --------------------------------------------------------------------------
// Inbound Policy: Pass subscription key for internal REST API call
// MCP → APIM REST API (subscription key) → Container App (MI token)
// --------------------------------------------------------------------------
var mcpPolicyXml = '<policies><inbound><base /><set-header name="Ocp-Apim-Subscription-Key" exists-action="override"><value>{{st-orders-internal-key}}</value></set-header></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'

resource mcpApiPolicy 'Microsoft.ApiManagement/service/apis/policies@2025-03-01-preview' = {
  parent: mcpApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: mcpPolicyXml
  }
  dependsOn: [internalKeyNamedValue]
}

// --------------------------------------------------------------------------
// Link MCP API to the existing "ST Orders Free" product
// so the same subscription key works for both REST and MCP.
// --------------------------------------------------------------------------
resource product 'Microsoft.ApiManagement/service/products@2024-05-01' existing = {
  parent: apim
  name: 'st-orders-free'
}

resource mcpProductApi 'Microsoft.ApiManagement/service/products/apis@2024-05-01' = {
  parent: product
  name: mcpApi.name
}

// --------------------------------------------------------------------------
// Outputs
// --------------------------------------------------------------------------
@description('MCP endpoint URL.')
output mcpEndpoint string = '${apim.properties.gatewayUrl}/st-orders-mcp/mcp'
