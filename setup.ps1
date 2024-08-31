# Set no cache directory for pip commands by passing it as a parameter
$PIP_NO_CACHE_DIR = "--no-cache-dir"

# Upgrade pip, wheel, and setuptools
Write-Host "Upgrading pip, wheel, and setuptools..."
pip install --upgrade pip wheel setuptools

# Upgrade pip without cache
Write-Host "Upgrading pip without cache..."
pip install $PIP_NO_CACHE_DIR --upgrade pip

# Install PyTorch packages from a specific index URL without cache
# Ref: https://stackoverflow.com/a/77208494
Write-Host "Installing PyTorch packages from the specified index URL..."
pip install $PIP_NO_CACHE_DIR torch --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers without cache
Write-Host "Installing sentence-transformers..."
pip install $PIP_NO_CACHE_DIR sentence-transformers

# Install the current package in editable mode
Write-Host "Installing the package in editable mode..."
pip install -e .


Write-Host "Installation and cleanup complete!"
