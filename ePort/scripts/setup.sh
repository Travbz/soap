#!/bin/bash
# Vending Machine Complete Setup Script
# Run this once on a fresh Raspberry Pi to configure everything automatically

set -e  # Exit on error

echo "=============================================="
echo "  Vending Machine - Complete Setup"
echo "=============================================="
echo ""
echo "This script will:"
echo "1. Install all dependencies"
echo "2. Configure customer display"
echo "3. Setup systemd service"
echo "4. Configure autostart"
echo ""
read -p "Press Enter to begin setup..."
echo ""

# Check if running on Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Project location: $PROJECT_ROOT"
echo ""

# ============================================
# Step 1: Install Python Dependencies
# ============================================
echo "Step 1/6: Installing Python dependencies..."

# Use requirements.txt for consistent versioning
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip3 install --user -r "$PROJECT_ROOT/requirements.txt"
else
    # Fallback: install with pinned versions
    echo "requirements.txt not found, installing with pinned versions..."
    pip3 install --user RPi.GPIO>=0.7.0 pyserial>=3.5
    pip3 install --user 'flask>=2.0.0,<3.0.0' python-engineio==4.9.0 python-socketio==5.11.0 flask-socketio==5.3.6
fi

echo "✓ Python dependencies installed"
echo ""

# ============================================
# Step 2: Install Display Dependencies
# ============================================
echo "Step 2/6: Installing display system (Chromium)..."
sudo apt update
sudo apt install -y chromium-browser unclutter
echo "✓ Chromium browser installed"
echo ""

# ============================================
# Step 3: Configure Display Autostart
# ============================================
echo "Step 3/6: Configuring display autostart..."
AUTOSTART_FILE="/etc/xdg/lxsession/LXDE-pi/autostart"
AUTOSTART_BACKUP="/etc/xdg/lxsession/LXDE-pi/autostart.backup.$(date +%Y%m%d-%H%M%S)"

# Backup existing autostart if it exists
if [ -f "$AUTOSTART_FILE" ]; then
    sudo cp "$AUTOSTART_FILE" "$AUTOSTART_BACKUP"
    echo "✓ Backed up existing autostart to $AUTOSTART_BACKUP"
fi

# Remove any existing vending machine display config
sudo sed -i '/# Customer Display/d' "$AUTOSTART_FILE" 2>/dev/null || true
sudo sed -i '/@unclutter -idle 0/d' "$AUTOSTART_FILE" 2>/dev/null || true
sudo sed -i '/@chromium-browser.*localhost:5000/d' "$AUTOSTART_FILE" 2>/dev/null || true

# Add display configuration
echo "Adding display configuration to autostart..."
sudo tee -a "$AUTOSTART_FILE" > /dev/null << 'EOF'

# Customer Display - Hide cursor
@unclutter -idle 0

# Customer Display - Chromium kiosk mode
@chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --check-for-update-interval=31536000 http://localhost:5000
EOF

echo "✓ Display autostart configured"
echo ""

# ============================================
# Step 4: Install Systemd Service
# ============================================
echo "Step 4/6: Installing vending machine service..."

# Update service file with correct path
SERVICE_FILE="$SCRIPT_DIR/vending-machine.service"
TEMP_SERVICE="/tmp/vending-machine.service.tmp"

# Replace WorkingDirectory with actual path
sed "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_ROOT|g" "$SERVICE_FILE" > "$TEMP_SERVICE"

# Copy to systemd
sudo cp "$TEMP_SERVICE" /etc/systemd/system/vending-machine.service
rm "$TEMP_SERVICE"

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable vending-machine.service

echo "✓ Vending machine service installed and enabled"
echo ""

# ============================================
# Step 5: Configure Desktop Auto-Login
# ============================================
echo "Step 5/6: Configuring desktop auto-login..."
echo ""
echo "For the display to work, desktop must auto-login on boot."
echo "After this script completes, run:"
echo "  sudo raspi-config"
echo "  → Boot Options → Desktop/CLI → Desktop Autologin"
echo ""
read -p "Press Enter to continue..."
echo ""

# ============================================
# Step 6: Test Installation
# ============================================
echo "Step 6/6: Testing installation..."
echo ""

# Test display server
echo "Testing display server (10 seconds)..."
timeout 10s python3 -m ePort.tests.test_display > /dev/null 2>&1 || true
echo "✓ Display server test complete"
echo ""

# Test payment system
echo "Testing payment protocol..."
python3 -m ePort.tests.test_payment > /dev/null 2>&1
echo "✓ Payment protocol tests passed"
echo ""

# Test multi-product system
echo "Testing multi-product system..."
python3 -m ePort.tests.test_multi_product > /dev/null 2>&1
echo "✓ Multi-product tests passed"
echo ""

# ============================================
# Setup Complete
# ============================================
echo "=============================================="
echo "  ✓ Setup Complete!"
echo "=============================================="
echo ""
echo "IMPORTANT: Next steps to activate the system:"
echo ""
echo "1. Configure desktop auto-login:"
echo "   sudo raspi-config"
echo "   → Boot Options → Desktop/CLI → Desktop Autologin"
echo ""
echo "2. Configure your products:"
echo "   nano $SCRIPT_DIR/config/products.json"
echo ""
echo "3. Reboot the Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "After reboot:"
echo "- Chromium will auto-launch showing customer display"
echo "- Vending machine service will start automatically"
echo "- Machine will be ready for transactions"
echo ""
echo "To view logs after reboot:"
echo "  sudo journalctl -u vending-machine -f"
echo ""
echo "To check service status:"
echo "  sudo systemctl status vending-machine"
echo ""
