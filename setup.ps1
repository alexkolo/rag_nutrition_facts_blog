# Upgrade pip, wheel, and setuptools
Write-Host "Upgrading pip, wheel, and setuptools..."
pip install --no-cache-dir --upgrade pip wheel setuptools

# Install PyTorch packages from a specific index URL without cache
# Ref: https://stackoverflow.com/a/77208494
Write-Host "Installing PyTorch packages from the specified index URL..."
pip install --no-cache-dir torch==2.4.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install the current package in editable mode
Write-Host "Installing the package in editable mode..."
pip install --no-cache-dir -e .


Write-Host "Installation and cleanup complete!"
