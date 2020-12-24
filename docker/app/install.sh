#!/bin/bash

python -m pip install pip &&
pip install -r /StockML/docker/app/requirements.txt &&

cd /StockML/lib/twstock &&
FLIT_ROOT_INSTALL=1 flit install &&
cd ../.. &&

echo "done"
