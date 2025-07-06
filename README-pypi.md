# MIArchive

Small internet archive for self-hosted, private archival.

For more comprehensive information about MIArchive, see the [full README on Codeberg](https://codeberg.org/LunarWatcher/MIArchive#readme). This README is a special PyPI README, because PyPI does not support the markdown features used in the main README.

## Requirements

* Linux-based server
* PostgreSQL
* Python 3.10+


## Installation

You can either do it manually:
```bash
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
miarchive setup
```
Or using an install script featuring the exact same commands:
```bash
bash <(curl -L https://codeberg.org/LunarWatcher/MIArchive/raw/branch/master/scripts/install.sh)
```

The bulk of the setup systems are scripted in Python for everyone's convenience.
