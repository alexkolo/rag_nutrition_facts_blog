#!/bin/bash

# Set --no-cache-dir as the default for all pip commands
export PIP_NO_CACHE_DIR=1

# Upgrade pip, wheel, and setuptools
echo "Upgrading pip, wheel, and setuptools..."
pip install --upgrade pip wheel setuptools

# Install PyTorch packages from a specific index URL without cache
# Ref: https://stackoverflow.com/a/77208494
echo "Installing PyTorch packages from the specified index URL..."
pip install torch==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install the current package in editable mode
echo "Installing the package in editable mode..."
pip install -e .

# save to requirements.txt
pip freeze --exclude-editable > requirements.txt

echo "Installation and cleanup complete!"
