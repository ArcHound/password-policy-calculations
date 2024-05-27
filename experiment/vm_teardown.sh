#!/bin/bash

RG=pw_policy_costs_analytics
vm_name=cd458deedd7ac0541be1e5178dbad4c5_runner_21380

az vm deallocate -n $vm_name -g $RG
