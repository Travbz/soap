#!/bin/bash
# Customer Display Setup Script
# Automates installation of display dependencies and Chromium kiosk mode

set -e  # Exit on error

echo "==========================================="
echo "Customer Display Setup"
echo "==========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. Install Python dependencies
echo "Step 1/5: Installing Python dependencies..."
pip3 install flask flask-socketio python-socketio --user
echo "✓ Python dependencies installed"
echo ""

# 2. Install Chromium and utilities
echo "Step 2/5: Installing Chromium browser..."
sudo apt update
sudo apt install -y chromium-browser unclutter
echo "✓ Chromium installed"
echo ""

# 3. Configure autostart
echo "Step 3/5: Configuring autostart..."
AUTOSTART_FILE="/etc/xdg/lxsession/LXDE-pi/autostart"
AUTOSTART_BACKUP="/etc/xdg/lxsession/LXDE-pi/autostart.backup"

# Backup existing autostart
if [ -f "$AUTOSTART_FILE" ]; then
    sudo cp "$AUTOSTART_FILE" "$AUTOSTART_BACKUP"
    echo "✓ Backed up existing autostart to $AUTOSTART_BACKUP"
fi

# Add display configuration
echo "Adding display configuration..."
sudo tee -a "$AUTOSTART_FILE" > /dev/null << 'EOF'

# Customer Display - Hide cursor
@unclutter -idle 0

# Customer Display - Chromium kiosk mode
@chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --check-for-update-interval=31536000 http://localhost:5000
EOF

echo "✓ Autostart configured"
echo ""

# 4. Enable desktop auto-login
echo "Step 4/5: Configuring desktop auto-login..."
echo "This requires raspi-config. After this script, run:"
echo "  sudo raspi-config"
echo "  → Boot Options → Desktop / CLI → Desktop Autologin"
echo ""
read -p "Press Enter to continue..."

# 5. Test display
echo "Step 5/5: Testing display server..."
cd ~/soap
echo "Starting display test (will run for 10 seconds)..."
timeout 10s python3 -m ePort.tests.test_display || true
echo ""

echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Reboot the Raspberry Pi: sudo reboot"
echo "2. After reboot, Chromium will auto-start in kiosk mode"
echo "3. Start the vending machine: python3 -m ePort.main"
echo ""
echo "To disable display:"
echo "  Edit ePort/config/__init__.py"
echo "  Set: DISPLAY_ENABLED = False"
echo ""
echo "To test without rebooting:"
echo "  python3 -m ePort.tests.test_display"
echo "  Then open: http://localhost:5000 in any browser"
echo ""
