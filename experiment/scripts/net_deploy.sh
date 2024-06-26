#!/bin/bash

az login
# az account set --subscription "Azure subscription 1"

region=northeurope
RG=pw_policy_costs_analytics 

vnet_name=myvnet
vnet_prefix=192.168.0.0/16
vnet_subnet_name=myvnetsubnet
vnet_subnet_prefix=192.168.1.0/24

az network vnet create -g $RG --name $vnet_name --address-prefix $vnet_prefix --subnet-name $vnet_subnet_name --subnet-prefix $vnet_subnet_prefix

pubip_name=mypubip
dns_name=cd458deedd7ac0541be1e5178dbad4c5

az network public-ip create -g $RG --name $pubip_name --dns-name $dns_name

nsg_name=nsg

az network nsg create -g $RG --name $nsg_name
az network nsg rule create \
    --resource-group $RG \
    --nsg-name $nsg_name \
    --name allow-ssh \
    --protocol tcp \
    --priority 1000 \
    --destination-port-range 22 \
    --access allow

nic_name=myNic

az network nic create -g $RG --name $nic_name --vnet-name $vnet_name --subnet $vnet_subnet_name --public-ip-address $pubip_name --network-security-group $nsg_name
