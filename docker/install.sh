#!/bin/bash

apt-get update
apt-get install git
git clone git clone https://github.com/HYChou0515/StockML.git

python -m pip install pip
pip install -r requirements.txt

cd lib/twstock
FLIT_ROOT_INSTALL=1 flit install
cd ../..
