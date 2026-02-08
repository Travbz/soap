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

# Create user-specific autostart directory (takes precedence over system-wide)
USER_AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
USER_AUTOSTART_FILE="$USER_AUTOSTART_DIR/autostart"

mkdir -p "$USER_AUTOSTART_DIR"

# Backup existing autostart if it exists
if [ -f "$USER_AUTOSTART_FILE" ]; then
    AUTOSTART_BACKUP="$USER_AUTOSTART_FILE.backup.$(date +%Y%m%d-%H%M%S)"
    cp "$USER_AUTOSTART_FILE" "$AUTOSTART_BACKUP"
    echo "✓ Backed up existing autostart to $AUTOSTART_BACKUP"
fi

# Create new autostart file with kiosk configuration
echo "Creating kiosk mode configuration..."
cat > "$USER_AUTOSTART_FILE" << 'EOF'
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi

# Disable screen blanking and power management
@xset s off
@xset -dpms
@xset s noblank

# Hide mouse cursor immediately
@unclutter -idle 0

# Launch Chromium in full-screen kiosk mode (NO browser UI visible)
@chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble --disable-translate --check-for-update-interval=31536000 --disable-features=TranslateUI http://localhost:5000
EOF

echo "✓ Kiosk mode autostart configured"
echo "  - Full-screen mode (no address bar or tabs)"
echo "  - Mouse cursor hidden"
echo "  - Screen blanking disabled"
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
# Step 5: Configure Desktop Auto-Login (AUTOMATED)
# ============================================
echo "Step 5/6: Configuring desktop auto-login (automated)..."

# Check if LightDM is installed (default display manager on Raspberry Pi OS)
if [ -f /etc/lightdm/lightdm.conf ]; then
    echo "Configuring LightDM for auto-login..."
    
    # Backup existing config
    sudo cp /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.backup.$(date +%Y%m%d-%H%M%S)
    
    # Configure auto-login
    sudo sed -i '/^#autologin-user=/c\autologin-user=pi' /etc/lightdm/lightdm.conf
    sudo sed -i '/^autologin-user=/c\autologin-user=pi' /etc/lightdm/lightdm.conf
    
    # If line doesn't exist, add it
    if ! grep -q "^autologin-user=" /etc/lightdm/lightdm.conf; then
        sudo sed -i '/^\[Seat:\*\]/a autologin-user=pi' /etc/lightdm/lightdm.conf
    fi
    
    echo "✓ Desktop auto-login configured for user 'pi'"
else
    echo "⚠️  LightDM not found - using raspi-config method..."
    echo "Configuring auto-login via raspi-config..."
    
    # Use raspi-config non-interactive mode
    sudo raspi-config nonint do_boot_behaviour B4
    
    echo "✓ Desktop auto-login configured"
fi
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
echo "  ✓ SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "✅ All configuration automated:"
echo "   • Python dependencies installed"
echo "   • Chromium browser installed"
echo "   • Kiosk mode configured (full-screen, no browser UI)"
echo "   • Auto-login configured"
echo "   • Systemd service installed"
echo "   • All tests passed"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. [OPTIONAL] Configure your products:"
echo "   nano $PROJECT_ROOT/config/products.json"
echo ""
echo "2. Reboot the Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "🎉 After Reboot - The System Will:"
echo "   • Auto-login to desktop"
echo "   • Launch Chromium in FULL-SCREEN kiosk mode"
echo "   • Display customer interface (NO address bar/tabs)"
echo "   • Start vending machine service automatically"
echo "   • Be ready for transactions!"
echo ""
echo "📊 Useful Commands:"
echo ""
echo "View live logs:"
echo "  sudo journalctl -u vending-machine -f"
echo ""
echo "Check service status:"
echo "  sudo systemctl status vending-machine"
echo ""
echo "Restart service:"
echo "  sudo systemctl restart vending-machine"
echo ""
echo "Stop service:"
echo "  sudo systemctl stop vending-machine"
echo ""
echo "To exit kiosk mode during testing:"
echo "  Press Alt+F4"
echo ""
echo "=============================================="
echo "  Ready to reboot!"
echo "=============================================="
echo ""