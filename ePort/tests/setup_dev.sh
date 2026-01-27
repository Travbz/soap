#!/bin/bash
# Setup development environment for testing display locally
# Uses uv for fast dependency management

set -e

echo "Setting up development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create venv with uv
echo "Creating virtual environment..."
uv venv

# Activate venv and install dependencies
echo "Installing dependencies..."
source .venv/bin/activate

# Install only what's needed for display testing (not RPi.GPIO)
uv pip install flask flask-socketio python-socketio

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the display test:"
echo "  source .venv/bin/activate"
echo "  python3 -m ePort.tests.test_display"
echo ""
echo "Then open: http://localhost:5000"
