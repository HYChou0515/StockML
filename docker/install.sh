#!/bin/bash

apt-key adv --keyserver keyserver.ubuntu.com --recv-key FDC247B7
echo 'deb https://repo.windscribe.com/ubuntu bionic main' | tee /etc/apt/sources.list.d/windscribe-repo.list
apt-get update
apt-get install -y git windscribe-cli expect
git clone https://github.com/HYChou0515/StockML.git

python -m pip install pip
pip install -r /tmp/requirements.txt

cd /StockML/lib/twstock
FLIT_ROOT_INSTALL=1 flit install
cd ../..
