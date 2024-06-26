resource "azurerm_linux_virtual_machine" "runner" {
  name                = "runner"
  resource_group_name = azurerm_resource_group.tf_rg.name
  location            = azurerm_resource_group.tf_rg.location
  size                = "Standard_NC6s_v3"
  admin_username      = "adminadmin"
  network_interface_ids = [
    azurerm_network_interface.public_vm_nic.id,
  ]

  admin_ssh_key {
    username   = "adminadmin"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }
}
