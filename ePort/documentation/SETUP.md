# Vending Machine Controller

A modular Python application for controlling a soap vending machine with integrated credit card payment processing via ePort Telemeter device.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd ePort
   pip3 install -r requirements.txt
   ```

2. **Run tests (without hardware):**
   ```bash
   python3 tests/test_payment.py
   ```

3. **Deploy to Raspberry Pi:**
   - Copy `ePort/` directory to Raspberry Pi
   - Follow Installation & Setup section below

## Installation & Setup

### Prerequisites

- **Raspberry Pi** with GPIO access (Raspberry Pi 3, 4, or newer recommended)
- **Python 3.7 or higher** (usually pre-installed on Raspberry Pi OS)
- **ePort Telemeter device** connected via USB serial (`/dev/ttyUSB0`)
- **Required Python packages:**
  - `RPi.GPIO` - For GPIO control
  - `pyserial` - For serial communication

### Step 1: Check Python Version

Verify Python 3 is installed:

```bash
python3 --version
```

You should see `Python 3.7.0` or higher. If not, install Python 3:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Install Dependencies

**Option 1: Manual Installation (Recommended)**

```bash
pip3 install RPi.GPIO pyserial
```

**Note:** If you get permission errors, use `pip3 install --user RPi.GPIO pyserial`

**Option 2: Using requirements.txt**

```bash
pip3 install -r requirements.txt
```

### Step 3: Copy Code to Raspberry Pi

Copy the entire `ePort/` directory to your Raspberry Pi:

```bash
# From your development machine:
scp -r ePort/ pi@raspberrypi.local:~/vending-machine/

# Or use git, USB drive, or any other method
```

### Step 4: Configure Hardware Settings

Edit `config/__init__.py` if your hardware pin assignments differ from defaults:

```python
# Machine hardware configuration
MOTOR_PIN = 17          # GPIO pin for motor control
FLOWMETER_PIN = 24      # GPIO pin for flowmeter input
PRODUCT_BUTTON_PIN = 4  # GPIO pin for product selection button
DONE_BUTTON_PIN = 27    # GPIO pin for done button

# Serial port settings
SERIAL_PORT = '/dev/ttyUSB0'  # Serial port for ePort device
```

**To find your serial port:**
```bash
ls -l /dev/ttyUSB*
# or
ls -l /dev/ttyACM*
```

### Step 5: Verify Serial Port Permissions

Make sure your user can access the serial port:

```bash
# Add user to dialout group (usually already done for 'pi' user)
sudo usermod -a -G dialout $USER
# Log out and log back in for changes to take effect

# Check permissions
ls -l /dev/ttyUSB0
```

### Step 6: Test Connection (Optional)

Run tests to verify code works (doesn't require hardware):

```bash
cd ~/vending-machine
python3 ePort/tests/test_payment.py
```

All tests should pass. See `TESTING.md` in the documentation directory for more information.

### Step 7: Run Manually (For Testing)

Before installing as a service, test manually:

```bash
cd ~/vending-machine
python3 -m ePort.main
```

Press `Ctrl+C` to stop. Check for errors in the output.

### Step 8: Install as Systemd Service

For production, install as a systemd service so it starts automatically on boot:

```bash
# Copy service file
sudo cp ePort/vending-machine.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable vending-machine.service

# Start the service
sudo systemctl start vending-machine.service

# Check status
sudo systemctl status vending-machine.service
```

The service will now:
- Start automatically on boot
- Restart automatically if it crashes
- Log to systemd journal

### Step 9: Verify Service is Running

Check service status:

```bash
sudo systemctl status vending-machine
```

View logs:

```bash
# Real-time logs
sudo journalctl -u vending-machine -f

# Recent logs (last 100 lines)
sudo journalctl -u vending-machine -n 100

# Logs from today
sudo journalctl -u vending-machine --since today
```

## Running Tests

See `TESTING.md` in the documentation directory for detailed testing instructions.

Quick test command:
```bash
python3 tests/test_payment.py
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u vending-machine -n 50
```

**Common issues:**
- Python path incorrect in service file
- Missing dependencies (`pip3 install RPi.GPIO pyserial`)
- Permission errors (check serial port permissions)
- GPIO access denied (should work for 'pi' user)

### Serial Port Not Found

**Check if device is connected:**
```bash
ls -l /dev/ttyUSB*
dmesg | tail  # Check kernel messages
```

**Common issues:**
- USB cable not connected
- Device not powered on
- Wrong port name (might be `/dev/ttyACM0` instead of `/dev/ttyUSB0`)
- Update `SERIAL_PORT` in `config/__init__.py`

### Permission Denied on Serial Port

**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### GPIO Permission Errors

**If you get GPIO permission errors:**
- Make sure you're running as user `pi` (not root)
- Check GPIO pins are not in use by another process
- Verify wiring connections

### Import Errors

**If you see import errors:**
- Verify you're in the correct directory
- Check Python version: `python3 --version`
- Reinstall dependencies: `pip3 install -r requirements.txt`

## Configuration

All configuration is in `config/__init__.py`:

- **Hardware pins** - GPIO pin assignments
- **Serial settings** - Port, baudrate, timeout
- **Product settings** - Price, calibration, description
- **Retry settings** - Error handling configuration

## Architecture

See `ARCHITECTURE.md` in the documentation directory for detailed architecture documentation.

## Documentation

- **Architecture Guide**: `ARCHITECTURE.md`
- **Testing Guide**: `TESTING.md`
- **Protocol Documentation**: `../docs/Serial ePort Protocol -Rev 18.pdf` (if docs moved)
