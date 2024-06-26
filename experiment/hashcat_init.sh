#!/bin/bash

sudo apt update
sudo apt install -y hashcat

if [ "$devs" == "0" ]; then
	echo "No GPU"
else
	echo "GPU!!"
	sudo apt install ubuntu-drivers-common
	sudo apt install nvidia-utils-535-server
	sudo apt install nvidia-cuda-toolkit
	# wget developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.1-1_all.deb
	# sudo apt install -y ./cuda-keyring_1.1-1_all.deb
	# sudo apt update
	# sudo apt -y install cuda-toolkit
fi

# reboot
