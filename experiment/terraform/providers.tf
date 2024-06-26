terraform {
  backend "local" {
    path = "../../../pw_terraform_state.tfstate"
  }
}

provider "azurerm" {
  features {}
}
