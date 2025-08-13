#!/usr/bin/bash

set -e

# Set up directory
cd /opt
sudo mkdir miarchive
sudo chown $USER miarchive
cd miarchive

# Set up venv
python3 -m venv env
source env/bin/activate

# Install MIA
pip3 install miarchive

# Set up environment
mia setup
