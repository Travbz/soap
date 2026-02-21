# Raspberry Pi 5 Hardware Setup Guide
Complete setup instructions for vending machine hardware

## Table of Contents
1. [Initial Pi Setup](#initial-pi-setup)
2. [ePort Connection](#eport-connection)
3. [Breadboard & GPIO Wiring](#breadboard--gpio-wiring)
4. [Software Installation](#software-installation)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## 1. Initial Pi Setup

### What You Have
- Raspberry Pi 5 8GB
- 128GB microSD card
- USB-C power supply (or powered USB from computer)
- ePort card reader
- 47-position breadboard
- Buttons (4 total: 3 product buttons + 1 done button)
- Jumper wires

### Step 1.1: Install Raspberry Pi OS

**On your computer:**

1. Download Raspberry Pi Imager: https://www.raspberrypi.com/software/
2. Insert the microSD card into your computer
3. Open Raspberry Pi Imager
4. Click "Choose Device" → Raspberry Pi 5
5. Click "Choose OS" → Raspberry Pi OS (64-bit) - **Full (Recommended)**
6. Click "Choose Storage" → Your 128GB SD card
7. Click the gear icon (⚙️) for advanced options:
   - Set hostname: `vending-pi`
   - Enable SSH (with password authentication)
   - Set username: `pi`
   - Set password: (your choice)
   - Configure WiFi (your network name and password)
   - Set locale settings (timezone, keyboard)
8. Click "Write" and wait for it to complete
9. Eject the SD card

### Step 1.2: Boot the Pi

1. Insert the microSD card into the Pi
2. Connect power (either USB-C power adapter OR USB-C from computer)
   - **Note:** Pi 5 needs 5V/5A for best performance, but can run on less for testing
3. Wait 2-3 minutes for first boot
4. Find the Pi's IP address:
   - Check your router's connected devices page, OR
   - Use `ping vending-pi.local` from your computer

### Step 1.3: Connect via SSH

```bash
ssh pi@vending-pi.local
# OR
ssh pi@<IP_ADDRESS>
```

Enter the password you set during imaging.

---

## 2. ePort Connection

### USB Port Selection

**For Raspberry Pi 5:**
- Use either **blue USB 3.0 port** (faster) or white USB 2.0 port
- **Does NOT matter which specific port** - all work the same
- The ePort will show up as `/dev/ttyUSB0` (or `/dev/ttyUSB1` if multiple USB serial devices)

### Connection Steps

1. **Power OFF the Pi** before connecting ePort (safer for hardware)
2. Connect ePort USB cable to any USB port on the Pi
3. Power ON the Pi
4. After boot, verify the connection:

```bash
ls -l /dev/ttyUSB*
```

**Expected output:**
```
crw-rw---- 1 root dialout 188, 0 Feb 21 10:30 /dev/ttyUSB0
```

5. Add your user to the `dialout` group (for serial port access):

```bash
sudo usermod -a -G dialout pi
```

6. **Reboot for group changes to take effect:**

```bash
sudo reboot
```

### Verify ePort Communication

After reboot, test the serial connection:

```bash
python3 -c "import serial; ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1); print('Success!')"
```

If you see "Success!" - ePort is properly connected! ✅

---

## 3. Breadboard & GPIO Wiring

### GPIO Pin Layout (Raspberry Pi 5)

The Pi 5 uses the same 40-pin GPIO header as Pi 4. **Pin numbering uses BCM mode** (not physical pin numbers).

```
     3.3V  (1) (2)  5V
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND
    GPIO4  (7) (8)  GPIO14
      GND  (9) (10) GPIO15
   GPIO17 (11) (12) GPIO18
   GPIO27 (13) (14) GND
   GPIO22 (15) (16) GPIO23
     3.3V (17) (18) GPIO24
   GPIO10 (19) (20) GND
    GPIO9 (21) (22) GPIO25
   GPIO11 (23) (24) GPIO8
      GND (25) (26) GPIO7
    GPIO0 (27) (28) GPIO1
    GPIO5 (29) (30) GND
    GPIO6 (31) (32) GPIO12
   GPIO13 (33) (34) GND
   GPIO19 (35) (36) GPIO16
   GPIO26 (37) (38) GPIO20
      GND (39) (40) GPIO21
```

### Your Configuration (from products.json)

| Component | GPIO Pin | Physical Pin | Purpose |
|-----------|----------|--------------|---------|
| **Product 1: Hand Soap** ||||
| Motor | GPIO 22 | Pin 15 | Controls pump |
| Flowmeter | GPIO 5 | Pin 29 | Measures volume |
| Button | GPIO 17 | Pin 11 | Dispense trigger |
| **Product 2: Dish Soap** ||||
| Motor | GPIO 18 | Pin 12 | Controls pump |
| Flowmeter | GPIO 25 | Pin 22 | Measures volume |
| Button | GPIO 23 | Pin 16 | Dispense trigger |
| **Product 3: Laundry Detergent** ||||
| Motor | GPIO 20 | Pin 38 | Controls pump |
| Flowmeter | GPIO 21 | Pin 40 | Measures volume |
| Button | GPIO 16 | Pin 36 | Dispense trigger |
| **Done Button** ||||
| Button | GPIO 27 | Pin 13 | Complete transaction |

### Breadboard Wiring Diagram

**For Testing (Simple Button Setup):**

Each button needs 2 wires:
1. One side to **GPIO pin** (see table above)
2. Other side to **GND** (ground)

**Button Wiring (Pull-up Configuration):**
```
Pi GPIO Pin → Button → GND

The software enables internal pull-up resistors, so:
- Button NOT pressed = HIGH (3.3V)
- Button pressed (connects to GND) = LOW (0V)
```

### Step-by-Step Wiring (Buttons Only for Testing)

**You'll need 8 jumper wires total:**

1. **Hand Soap Button:**
   - Wire 1: Pi Pin 11 (GPIO 17) → Breadboard row A1
   - Wire 2: Breadboard row A2 → Pi Pin 6 (GND)
   - Button: Spans rows A1-A2 on breadboard

2. **Dish Soap Button:**
   - Wire 1: Pi Pin 16 (GPIO 23) → Breadboard row B1
   - Wire 2: Breadboard row B2 → Pi Pin 9 (GND)
   - Button: Spans rows B1-B2 on breadboard

3. **Laundry Detergent Button:**
   - Wire 1: Pi Pin 36 (GPIO 16) → Breadboard row C1
   - Wire 2: Breadboard row C2 → Pi Pin 14 (GND)
   - Button: Spans rows C1-C2 on breadboard

4. **Done Button:**
   - Wire 1: Pi Pin 13 (GPIO 27) → Breadboard row D1
   - Wire 2: Breadboard row D2 → Pi Pin 20 (GND)
   - Button: Spans rows D1-D2 on breadboard

### Motor and Flowmeter Wiring (For Full System)

**Motors (3 total):**
- Each motor needs a **motor driver/relay** (not direct GPIO connection)
- GPIO output → Relay IN → Relay switches 12V power to motor
- **DO NOT connect motors directly to GPIO** - they'll damage the Pi!

**Flowmeters (3 total):**
- Flowmeter Signal → GPIO pin (see table)
- Flowmeter VCC → 5V (Pi Pin 2 or 4)
- Flowmeter GND → GND (Pi Pin 6, 9, 14, 20, 25, 30, 34, or 39)

---

## 4. Software Installation

### Step 4.1: Update System

```bash
ssh pi@vending-pi.local
sudo apt update && sudo apt upgrade -y
```

### Step 4.2: Install Git and Python Dependencies

```bash
# Install Git
sudo apt install -y git

# Python should already be installed (Python 3.11 on Pi OS Bookworm)
python3 --version
```

### Step 4.3: Clone the Repository

```bash
cd ~
git clone https://github.com/Travbz/soap.git
cd soap
```

### Step 4.4: Checkout the Latest Fix Branch

```bash
git checkout fix/simplify-display-logic
```

### Step 4.5: Run Automated Setup

The setup script will:
- Install Python dependencies (Flask, SocketIO, pyserial, RPi.GPIO, etc.)
- Configure systemd service for auto-start
- Set up kiosk mode for the display
- Configure desktop auto-login

```bash
python3 -m ePort.main
```

The first run will automatically trigger setup. Follow any prompts.

**OR run setup manually:**

```bash
cd ~/soap/ePort/scripts
chmod +x setup.sh
./setup.sh
```

### Step 4.6: Reboot

```bash
sudo reboot
```

After reboot, the vending machine should auto-start!

---

## 5. Testing

### Test 1: Check Service Status

```bash
sudo systemctl status vending-machine
```

**Expected:** Active (running) in green

### Test 2: View Logs

```bash
sudo journalctl -u vending-machine -f
```

Look for:
- `Serial connection established`
- `GPIO initialized successfully`
- `Display server started on http://localhost:5000`
- No error messages

### Test 3: Test Display (Locally on Pi)

If you have a monitor connected to the Pi:
- Chromium should auto-launch in kiosk mode
- Display should show "INSERT CARD" screen

### Test 4: Test Display (From Your Computer)

Find the Pi's IP address:
```bash
hostname -I
```

On your computer, open browser to:
```
http://<PI_IP_ADDRESS>:5000
```

You should see the vending machine display!

### Test 5: Test Buttons (Without ePort)

You can test button detection without the ePort running:

```python
python3
>>> import RPi.GPIO as GPIO
>>> GPIO.setmode(GPIO.BCM)
>>> GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
>>> GPIO.input(17)  # Should return 1 (not pressed)
# Now press the button
>>> GPIO.input(17)  # Should return 0 (pressed)
>>> GPIO.cleanup()
>>> exit()
```

Repeat for each button GPIO pin.

### Test 6: Full System Test

1. Insert a test card into the ePort
2. The display should change to "AUTHORIZING"
3. After approval, display shows "SELECT PRODUCT"
4. Press a product button - motor should run (if connected)
5. Release button - motor stops
6. Press "Done" button
7. Receipt displays for 10 seconds
8. Returns to "INSERT CARD"

---

## 6. Troubleshooting

### Issue: ePort not detected (`/dev/ttyUSB0` doesn't exist)

**Fix:**
```bash
# Check if USB device is detected
lsusb

# Check kernel messages
dmesg | grep tty

# Try different USB port
# Unplug and replug ePort
```

### Issue: Permission denied on `/dev/ttyUSB0`

**Fix:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout pi
sudo reboot
```

### Issue: GPIO "pins in use" or "conflicting edge detection"

**Fix:**
```bash
# Stop the service
sudo systemctl stop vending-machine

# Clean up GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.cleanup()"

# Restart service
sudo systemctl start vending-machine
```

### Issue: Display not showing

**Fix:**
```bash
# Check if service is running
sudo systemctl status vending-machine

# Check Flask/display errors
sudo journalctl -u vending-machine | grep -i error

# Check if port 5000 is listening
sudo netstat -tlnp | grep 5000
```

### Issue: Buttons not working

**Test individual button:**
```bash
# Monitor GPIO events
gpio -g mode 17 in
gpio -g read 17  # Should show 1 when not pressed, 0 when pressed
```

**Check wiring:**
- Ensure button is connected: GPIO pin → Button → GND
- Check breadboard connections are secure
- Verify you're using correct GPIO pin numbers (BCM, not physical)

### Issue: WebSocket errors in logs

**Fix:**
```bash
cd ~/soap
pip3 install -r ePort/requirements.txt  # Installs eventlet and simple-websocket
sudo systemctl restart vending-machine
```

---

## Quick Reference Commands

```bash
# View live logs
sudo journalctl -u vending-machine -f

# Restart service
sudo systemctl restart vending-machine

# Stop service (for manual testing)
sudo systemctl stop vending-machine

# Run manually (for debugging)
cd ~/soap
python3 -m ePort.main

# Update code from GitHub
cd ~/soap
git pull
sudo systemctl restart vending-machine

# Check GPIO pin status
gpio readall
```

---

## Next Steps

Once hardware is working:
1. Calibrate flowmeters (`pulses_per_unit` in `products.json`)
2. Adjust pricing (`price_per_unit` in `products.json`)
3. Test full transaction flow with real credit cards
4. Monitor for any errors in production

---

## Support

If you encounter issues not covered here:
1. Check logs: `sudo journalctl -u vending-machine -n 100`
2. Review error messages carefully
3. Check hardware connections
4. Verify ePort is powered and connected
5. Test individual components in isolation

Good luck with your setup! 🎉
