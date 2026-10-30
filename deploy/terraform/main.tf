terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "maize" {
  name     = "maize-monitor-rg"
  location = "North Europe"
}

resource "azurerm_log_analytics_workspace" "maize" {
  name                = "maize-monitor-logs"
  location            = azurerm_resource_group.maize.location
  resource_group_name = azurerm_resource_group.maize.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "maize" {
  name                       = "maize-monitor-env"
  location                   = azurerm_resource_group.maize.location
  resource_group_name        = azurerm_resource_group.maize.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.maize.id
}

resource "azurerm_container_app" "maize" {
  name                         = "maize-monitor"
  container_app_environment_id = azurerm_container_app_environment.maize.id
  resource_group_name          = azurerm_resource_group.maize.name
  revision_mode                = "Single"

  template {
    container {
      name   = "maize-monitor"
      image  = "ghcr.io/margaretjohn14-alt/maize-monitor-platform:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
    min_replicas = 0
    max_replicas = 1
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

output "app_url" {
  value = "https://${azurerm_container_app.maize.latest_revision_fqdn}"
}