targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Container image name for the API service')
param apiImageName string = ''

// Tags that should be applied to all resources
var tags = {
  'azd-env-name': environmentName
}

// Generate a unique token for resource naming
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

// Container Apps environment and supporting resources
module containerApps './modules/container-apps-environment.bicep' = {
  name: 'container-apps'
  scope: rg
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

// Container Registry
module containerRegistry './modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

// Container App for API
module api './modules/container-app.bicep' = {
  name: 'container-app-api'
  scope: rg
  params: {
    name: 'fristenkalender-api'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerApps.outputs.environmentId
    imageName: !empty(apiImageName) ? apiImageName : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryName: containerRegistry.outputs.name
  }
}

// Outputs for azd
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = containerApps.outputs.environmentId
output AZURE_CONTAINER_APPS_ENVIRONMENT_NAME string = containerApps.outputs.environmentName
output AZURE_RESOURCE_GROUP string = rg.name
output SERVICE_API_ENDPOINT_URL string = 'https://${api.outputs.fqdn}'
