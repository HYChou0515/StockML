#!/bin/bash

echo h1 $WINDSCRIBE_USR
echo h2 $WINDSCRIBE_PASS
envsubst < /windscribe_login.template > /windscribe_login &&
python -m pip install pip &&
pip install -r /StockML/docker/app/requirements.txt &&

cd /StockML/lib/twstock &&
FLIT_ROOT_INSTALL=1 flit install &&
cd ../.. &&

/etc/init.d/windscribe-cli start &&
expect /windscribe_login &&

echo "done"
