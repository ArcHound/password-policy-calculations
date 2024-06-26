#!/bin/bash

# az login
# az account set --subscription "Azure subscription 1"

region=northeurope
RG=pw_policy_costs_analytics 

vm_name=cd458deedd7ac0541be1e5178dbad4c5_runner
vm_image=Debian11
vm_size=Standard_B1s
vm_admin_name=adminadmin

nic_name=myNic # see the net_deploy.sh 

# az vm image list -o table --publisher Debian  
# az vm list-sizes -l $region -o table

az vm create \
	-g $RG \
	-n $vm_name \
	--image $vm_image \
	--admin-username $vm_admin_name \
	--size $vm_size \
	--generate-ssh-keys \
	--nics $nic_name \
	--location $region \
	--nic-delete-option Detach \
	--os-disk-delete-option delete 

ip=$(az network public-ip list | jq 'first(map(.ipAddress)) | first' | tr -d '"')

scp -oStrictHostKeyChecking=no -r full/ halved/ runcat.sh hashcat_init.sh $vm_admin_name@$ip:/home/$vm_admin_name/

ssh -oStrictHostKeyChecking=no $vm_admin_name@$ip /home/$vm_admin_name/hashcat_init.sh

# reboot the vm
az vm restart \
	-g $RG \
	-n $vm_name

az vm wait \
	--custom "instanceView.statuses[?code=='PowerState/running']" \
	-g $RG
	--name $vm_name

ssh -oStrictHostKeyChecking=no $vm_admin_name@$ip /home/$vm_admin_name/runcat.sh

