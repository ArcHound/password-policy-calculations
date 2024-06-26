resource "azurerm_virtual_network" "vm_vnet" {
  name                = "mytf_vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.tf_rg.location
  resource_group_name = azurerm_resource_group.tf_rg.name
  depends_on          = [azurerm_resource_group.tf_rg]
}

resource "azurerm_subnet" "vnet_subnet" {
  name                 = "mytf_subnet2"
  resource_group_name  = azurerm_resource_group.tf_rg.name
  virtual_network_name = azurerm_virtual_network.vm_vnet.name
  address_prefixes     = ["10.0.3.0/24"]
  depends_on           = [azurerm_virtual_network.vm_vnet]
}

resource "azurerm_public_ip" "runner_public_ip" {
  name                = "runner_public_ip"
  resource_group_name = azurerm_resource_group.tf_rg.name
  location            = azurerm_resource_group.tf_rg.location
  allocation_method   = "Static"
  depends_on          = [azurerm_subnet.vnet_subnet]
}

resource "azurerm_network_security_group" "tf_nsg" {
  name                = "tf_nsg"
  location            = azurerm_resource_group.tf_rg.location
  depends_on          = [azurerm_subnet.vnet_subnet]
  resource_group_name = azurerm_resource_group.tf_rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    source_address_prefix      = "0.0.0.0/0"
    destination_port_range     = "22"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "public_vm_nic" {
  name                = "tf_vnet_nic"
  location            = azurerm_resource_group.tf_rg.location
  resource_group_name = azurerm_resource_group.tf_rg.name
  depends_on          = [azurerm_subnet.vnet_subnet, azurerm_public_ip.runner_public_ip]

  ip_configuration {
    name                          = "public_vm_ip"
    subnet_id                     = azurerm_subnet.vnet_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.runner_public_ip.id
  }
}

resource "azurerm_network_interface_security_group_association" "nsg_binding" {
  network_interface_id      = azurerm_network_interface.public_vm_nic.id
  network_security_group_id = azurerm_network_security_group.tf_nsg.id
  depends_on                = [azurerm_network_interface.public_vm_nic, azurerm_network_security_group.tf_nsg]
}
