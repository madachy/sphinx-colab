#!/bin/bash
# setup.sh - Setup script for GitHub Codespaces

echo "Setting up Colab to Sphinx converter..."

# Install Python dependencies
pip install sphinx sphinx-rtd-theme beautifulsoup4

# Install Pandoc (optional but recommended)
sudo apt update
sudo apt install -y pandoc

echo "✓ Setup complete!"
echo "Run: python colab_to_sphinx.py"
