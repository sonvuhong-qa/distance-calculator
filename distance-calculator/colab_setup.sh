#!/bin/bash
# Setup script for Google Colab
echo "Setting up environment for Distance Calculator..."
apt-get update
apt-get install -y chromium-browser chromium-chromedriver
pip install virtualenv
virtualenv .venv
./.venv/bin/pip install -r requirements.txt
echo "Setup complete. You can now run the tool."
