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
      "description": "Gentle hand wash soap",
      "status": "AVAILABLE",
      "message": "",
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

### Product fields and expected input types

- `products` (`array[object]`, required): List of product definitions.
- `id` (`string`, required): Unique product ID (example: `soap_hand`).
- `name` (`string`, required): Customer-facing product name.
- `description` (`string`, optional): Internal or display description.
- `status` (`string`, optional): Product availability. Use:
  - `AVAILABLE` for normal operation
  - `OOO` for out-of-order (disables product tile/button)
- `message` (`string`, optional): Message shown on out-of-order tile when `status` is `OOO`.
- `price_per_unit` (`number`, required): Price per unit (example: `0.15`).
- `unit` (`string`, required): Unit label shown to customer (example: `oz`).
- `motor_pin` (`integer`, required): GPIO output pin for motor.
- `flowmeter_pin` (`integer`, required): GPIO input pin for flowmeter sensor.
- `button_pin` (`integer`, required): GPIO input pin for product selection button.
- `pulses_per_unit` (`number`, required): Flowmeter calibration value.

### Validation rules

- `id` must be unique across all products.
- `motor_pin`, `flowmeter_pin`, and `button_pin` must each be unique across all products.
- `price_per_unit` and `pulses_per_unit` must be greater than `0`.
- If `status` is omitted, it defaults to `AVAILABLE`.
- If `message` is omitted, it defaults to an empty string.

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
