# Vending Machine Setup Guide

---

## Quick Start

**Run the main program:**

```bash
python3 -m ePort.main
```

That's it. Setup runs automatically on first launch.

After setup completes, reboot:
```bash
sudo reboot
```

---

## What Happens Automatically

When you run `main.py` for the first time, it:

1. Detects missing dependencies
2. Runs the setup script automatically
3. Installs Python packages (RPi.GPIO, pyserial, Flask)
4. Installs Chromium browser
5. Configures display to launch on boot
6. Installs systemd service
7. Runs tests

Then you just reboot and the system is ready.

---

## Product Configuration

Edit `config/products.json`:

```json
{
  "products": [
    {
      "id": "soap_hand",
      "name": "Hand Soap",
      "price_per_unit": 0.15,
      "unit": "oz",
      "motor_pin": 17,
      "flowmeter_pin": 24,
      "button_pin": 4,
      "pulses_per_unit": 5.4
    }
  ]
}
```

Add more products as needed. No duplicate pins or IDs allowed.

---

## Troubleshooting

### Service not starting
```bash
sudo journalctl -u vending-machine -n 50
```

### Serial port not found
```bash
ls -l /dev/ttyUSB*
sudo usermod -a -G dialout $USER  # then log out/in
```

### Display not showing
```bash
chromium-browser --version
```

### Manual setup
If auto-setup fails:
```bash
cd ~/soap/ePort/scripts
./setup.sh
```

---

## Verify Installation

```bash
# Check service
sudo systemctl status vending-machine

# View logs
sudo journalctl -u vending-machine -f

# Test display
curl http://localhost:5000/health
```

---

## More Documentation

- `ARCHITECTURE.md` - System design
- `TESTING.md` - How to test
- `PRD-CustomerDisplay.md` - Display system
- `SDLC.md` - Development workflow
