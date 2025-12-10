@description('The location for the Container App')
param location string

@description('Tags to apply to the resources')
param tags object

@description('Name of the Container App')
param name string

@description('Container Apps Environment ID')
param containerAppsEnvironmentId string

@description('Container image to deploy')
param imageName string

@description('Container Registry login server')
param containerRegistryLoginServer string

@description('Container Registry name')
param containerRegistryName string

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: containerRegistryName
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: [
            'https://fristenkalender.hochfrequenz.de'
            'http://localhost:3000'
            'http://localhost:5173'
            'https://fristenkalender.stage.hochfrequenz.de'
            'https://brave-ocean-076b69903.4.azurestaticapps.net'
            'https://*.westeurope.4.azurestaticapps.net'
          ]
          allowedMethods: ['GET', 'POST', 'OPTIONS']
          allowedHeaders: ['*']
          maxAge: 86400
        }
      }
      registries: [
        {
          server: containerRegistryLoginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: imageName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output name string = containerApp.name
