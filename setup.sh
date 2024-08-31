#!/bin/bash

# Set --no-cache-dir as the default for all pip commands
export PIP_NO_CACHE_DIR=1

# Upgrade pip, wheel, and setuptools
echo "Upgrading pip, wheel, and setuptools..."
pip install --upgrade pip wheel setuptools

# Upgrade pip without cache
echo "Upgrading pip without cache..."
pip install --no-cache-dir --upgrade pip

# Install PyTorch packages from a specific index URL without cache
# Ref: https://stackoverflow.com/a/77208494
echo "Installing PyTorch packages from the specified index URL..."
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers without cache
echo "Installing sentence-transformers..."
pip install --no-cache-dir sentence-transformers

# Install the current package in editable mode
echo "Installing the package in editable mode..."
pip install -e .

echo "Installation and cleanup complete!"
