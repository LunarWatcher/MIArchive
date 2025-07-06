#!/usr/bin/bash

set -e

cd /opt
sudo mkdir miarchive 

sudo chown $USER miarchive
cd miarchive

python3 -m venv env
source env/bin/activate

pip3 install miarchive

