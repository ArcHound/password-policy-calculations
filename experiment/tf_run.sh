#!/bin/bash

# first parameter - either "halved" or "full" to specify what experiment to run

# az login
# az account set --subscription "Azure subscription 1"

cd terraform

terraform init
terraform apply -auto-approve

cd ..

# can't be bothered
RG=tf_rg
vm_admin_name=adminadmin
vm_name=runner
ip=$(az network public-ip list -g $RG | jq 'first(map(.ipAddress)) | first' | tr -d '"')

scp -oStrictHostKeyChecking=no -r full/ halved/ runcat.sh hashcat_init.sh $vm_admin_name@$ip:/home/$vm_admin_name/

ssh -oStrictHostKeyChecking=no $vm_admin_name@$ip /home/$vm_admin_name/hashcat_init.sh

# reboot the vm
az vm restart \
	-g $RG \
	-n $vm_name

az vm wait \
	--custom "instanceView.statuses[?code=='PowerState/running']" \
	-g $RG \
	--name $vm_name

ssh -oStrictHostKeyChecking=no $vm_admin_name@$ip /home/$vm_admin_name/runcat.sh $1

scp -oStrictHostKeyChecking=no $vm_admin_name@$ip:/home/$vm_admin_name/benchmark.txt . 

# ugly hack to destroy vm ASAP
mv terraform/vms.tf .
cd terraform
terraform apply -auto-approve
cd ..
mv vms.tf terraform/vms.tf
