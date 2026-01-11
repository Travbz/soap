# Vending Machine Controller

A modular Python application for controlling a soap vending machine with integrated credit card payment processing via ePort Telemeter device.

## Overview

This system controls a vending machine that dispenses liquid soap by weight. It integrates with an ePort Telemeter card reader for credit card transactions using the Serial ePort Protocol. The application is designed to run continuously on a Raspberry Pi, monitoring for customer interactions and processing payments.

## Architecture

### Directory Structure

```
ePort/
├── config/              # Configuration constants
│   └── __init__.py      # CRC table, protocol constants, hardware pins, product settings
├── src/                 # Core application code
│   ├── machine.py       # MachineController - GPIO, motors, sensors, dispensing logic
│   └── payment.py       # EPortProtocol - ePort communication and CRC calculation
├── tests/               # Testing infrastructure
│   ├── mocks.py         # MockGPIO and MockSerial for testing without hardware
│   └── test_payment.py  # Unit tests for payment protocol
├── deployment.md        # Deployment instructions
└── vending-machine.service  # Systemd service file
```

### Components

#### 1. **Payment Handler (`src/payment.py`)**

The `EPortProtocol` class handles all communication with the ePort card reader device:

- **CRC Calculation**: Implements the CRC16 algorithm from Serial ePort Protocol Appendix B
- **Protocol Commands**: Status, Reset, Authorization Request, Transaction Result
- **Serial Communication**: Manages serial port communication with the ePort device

Key methods:
- `calculate_crc16()`: Calculates CRC16 checksum using the protocol's lookup table
- `status()`: Polls ePort device status
- `request_authorization()`: Initiates credit card authorization
- `send_transaction_result()`: Completes a sale transaction
- `get_transaction_id()`: Retrieves transaction ID after sale

#### 2. **Machine Controller (`src/machine.py`)**

The `MachineController` class handles all hardware interactions:

- **GPIO Management**: Controls motors, reads sensors and buttons
- **Flowmeter Integration**: Tracks product dispensed by weight
- **Motor Control**: Controls dispensing motor
- **Button Monitoring**: Handles product selection and completion buttons

Key methods:
- `start_dispensing()`: Initializes dispensing mode with callbacks
- `control_motor()`: Turns motor on/off
- `get_dispense_info()`: Returns current ounces and price
- `reset()`: Resets dispense counters

#### 3. **Configuration (`config/__init__.py`)**

Centralized configuration includes:

- **CRC Table**: Complete lookup table for CRC16 calculation
- **Protocol Constants**: RS, GS, CR, ACK, NAK separators
- **Hardware Pins**: GPIO pin assignments
- **Product Settings**: Price per ounce, calibration, product description
- **Serial Settings**: Port, baudrate, timeout

### Data Flow

1. **Initialization**: System starts, initializes GPIO and serial port
2. **Status Polling**: Continuously polls ePort device status
3. **Customer Interaction**: 
   - Customer swipes card → Authorization requested
   - If approved → Dispensing mode enabled
   - Customer presses button → Motor activates
   - Flowmeter tracks ounces dispensed
   - Customer presses done → Transaction result sent to ePort
4. **Transaction Completion**: Transaction ID retrieved and system resets

## Current Limitations

Currently, the system supports **one product** (hand soap). The configuration is hardcoded for a single product offering.

## Extending for Multiple Products

To support multiple soap products, you'll need to modify several components:

### Step 1: Update Configuration

Edit `ePort/config/__init__.py` to support multiple products:

```python
# Product configuration - Multiple products
PRODUCTS = {
    'hand_soap': {
        'id': '1',
        'name': 'Hand Soap',
        'description': 'oz hand wash',
        'price_per_ounce': 0.15,
        'motor_pin': 17,
        'flowmeter_pin': 24,
        'button_pin': 4,
    },
    'dish_soap': {
        'id': '2',
        'name': 'Dish Soap',
        'description': 'oz dish soap',
        'price_per_ounce': 0.12,
        'motor_pin': 18,  # Different pins for second product
        'flowmeter_pin': 25,
        'button_pin': 5,
    },
    # Add more products as needed
}

# Keep legacy single product config for backward compatibility
PRODUCT_PRICE = 0.15
PRODUCT_UNIT = 'oz hand wash'
FLOWMETER_PULSES_PER_OUNCE = 5.4
```

### Step 2: Create Product Selection Logic

Create a new file `ePort/src/product_selector.py`:

```python
"""
Product selection and management
"""

from typing import Dict, List
from ..config import PRODUCTS
from .machine import MachineController


class ProductManager:
    """Manages multiple products and their controllers"""
    
    def __init__(self, gpio):
        self.gpio = gpio
        self.products = PRODUCTS
        self.controllers: Dict[str, MachineController] = {}
        self.current_product: str = None
        
        # Initialize controllers for each product
        for product_id, config in self.products.items():
            self.controllers[product_id] = MachineController(
                gpio=gpio,
                motor_pin=config['motor_pin'],
                flowmeter_pin=config['flowmeter_pin'],
                product_button_pin=config['button_pin'],
                done_button_pin=27,  # Shared done button
                price_per_ounce=config['price_per_ounce'],
                pulses_per_ounce=5.4,  # Same calibration for all
                product_unit=config['description']
            )
    
    def select_product(self, product_id: str) -> bool:
        """Select a product for dispensing"""
        if product_id in self.controllers:
            self.current_product = product_id
            return True
        return False
    
    def get_current_controller(self) -> MachineController:
        """Get controller for currently selected product"""
        if self.current_product:
            return self.controllers[self.current_product]
        return None
    
    def list_products(self) -> List[Dict]:
        """List all available products"""
        return [
            {
                'id': product_id,
                'name': config['name'],
                'price': config['price_per_ounce'],
            }
            for product_id, config in self.products.items()
        ]
```

### Step 3: Update Main Application

Modify your main application loop to:

1. **Display product selection**: Show available products (LEDs, display, or buttons)
2. **Handle product selection**: Wait for customer to select a product
3. **Initialize product controller**: Use selected product's configuration
4. **Process transaction**: Use selected product's controller for dispensing
5. **Complete transaction**: Use selected product's ID and price

Example integration pattern:

```python
from ePort.src.payment import EPortProtocol
from ePort.src.product_selector import ProductManager

# Initialize
payment = EPortProtocol(serial_connection)
products = ProductManager(gpio)

# In main loop:
# 1. Customer selects product (via button, display, etc.)
selected_product = 'hand_soap'  # From user input
products.select_product(selected_product)

# 2. Process authorization
payment.request_authorization(amount_cents)

# 3. Get controller for selected product
controller = products.get_current_controller()

# 4. Dispense using selected product's controller
controller.start_dispensing(...)

# 5. Complete transaction with product info
product_config = products.products[selected_product]
payment.send_transaction_result(
    quantity=1,
    price_cents=int(controller.total_price * 100),
    item_id=product_config['id'],
    description=product_config['description']
)
```

### Step 4: Hardware Considerations

For multiple products, you'll need:

- **Separate GPIO pins** for each product's:
  - Motor control
  - Flowmeter input
  - Product selection button
- **Shared resources**:
  - Done button (can be shared)
  - ePort device (shared)
  - Serial port (shared)

### Step 5: Update Tests

Extend `tests/test_payment.py` to test multiple products:

```python
def test_multiple_products():
    """Test transaction with different products"""
    # Test each product configuration
    for product_id, config in PRODUCTS.items():
        # Test transaction result with product ID
        ...
```

## Installation & Setup

### Prerequisites

- Raspberry Pi with GPIO access
- Python 3.7+
- ePort Telemeter device connected via USB serial
- Required Python packages:
  ```
  RPi.GPIO
  pyserial
  ```

### Installation Steps

1. **Clone/copy code to Raspberry Pi:**
   ```bash
   scp -r ePort/ README.md pi@raspberrypi.local:~/vending-machine/
   ```

2. **Install dependencies:**
   ```bash
   cd ePort
   # Option 1: Install from requirements.txt (recommended)
   pip3 install -r requirements.txt
   
   # Option 2: Install manually
   pip3 install RPi.GPIO pyserial
   ```

3. **Configure hardware pins** (if different from defaults):
   Edit `ePort/config/__init__.py` with your GPIO pin assignments

4. **Install as systemd service:**
   ```bash
   sudo cp ePort/vending-machine.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable vending-machine.service
   sudo systemctl start vending-machine.service
   ```

5. **Run manually (for testing):**
   ```bash
   cd ~/vending-machine
   python3 -m ePort.main
   # Or:
   cd ~/vending-machine/ePort
   python3 main.py
   ```

See `SETUP.md` in this directory for detailed installation and setup instructions.

### Entry Point

The main entry point is `ePort/main.py`. This file:
- Initializes GPIO and serial connections
- Creates instances of `EPortProtocol` and `MachineController`
- Runs the continuous monitoring loop
- Handles customer transactions from start to finish

## Running Tests

Tests can be run without hardware using mocks:

```bash
# Run all tests
python3 tests/test_payment.py

# Or with pytest
pytest tests/ -v
```

Key tests:
- **CRC Calculation**: Verifies CRC matches protocol specification
- **Status Command**: Tests ePort status polling
- **Transaction Result**: Tests transaction completion with CRC

## Maintenance

### Monitoring

Check service status:
```bash
sudo systemctl status vending-machine
```

View logs:
```bash
# Real-time logs
sudo journalctl -u vending-machine -f

# Recent logs
sudo journalctl -u vending-machine -n 100

# Logs from today
sudo journalctl -u vending-machine --since today
```

### Common Issues

#### 1. **CRC Failures**

If transactions fail with CRC errors:
- Verify CRC table is correct in `config/__init__.py`
- Check that command construction matches protocol specification
- Use `test_payment.py` to verify CRC calculation

#### 2. **Serial Communication Issues**

If ePort device not responding:
- Check serial port: `ls -l /dev/ttyUSB*`
- Verify baudrate matches (9600 8-N-1)
- Check cable connections
- Review serial port permissions

#### 3. **GPIO Issues**

If hardware not responding:
- Verify GPIO pin assignments in config
- Check wiring connections
- Test GPIO pins manually
- Review RPi.GPIO permissions

#### 4. **Service Won't Start**

If systemd service fails:
- Check logs: `sudo journalctl -u vending-machine -n 50`
- Verify Python path in service file
- Check file permissions
- Verify all dependencies installed

### Calibration

Flowmeter calibration (`FLOWMETER_PULSES_PER_OUNCE`):
- Measure actual ounces dispensed
- Count pulses received
- Calculate: `pulses_per_ounce = total_pulses / total_ounces`
- Update in `config/__init__.py`

### Updates

To update code:
1. Stop service: `sudo systemctl stop vending-machine`
2. Update code files
3. Run tests: `python3 tests/test_payment.py`
4. Start service: `sudo systemctl start vending-machine`

## Protocol Reference

This implementation follows the **Serial ePort Protocol - Revision 18** specification.

Key protocol details:
- **Baudrate**: 9600 8-N-1 (no flow control)
- **CRC Algorithm**: CRC16 with lookup table (see Appendix B)
- **Command Format**: ASCII commands with CRC and CR termination
- **Status Polling**: Recommended every few seconds during idle

For detailed protocol documentation, refer to `Serial ePort Protocol -Rev 18.pdf`.

## Development

### Code Structure

The codebase follows a modular architecture:

- **Separation of Concerns**: Payment logic separate from machine logic
- **Dependency Injection**: Hardware interfaces passed as parameters (enables testing)
- **Configuration Centralization**: All settings in `config/`
- **Testability**: Mocks enable testing without hardware

### Adding Features

1. **New Protocol Commands**: Add methods to `EPortProtocol` class
2. **New Hardware**: Extend `MachineController` class
3. **Configuration Changes**: Update `config/__init__.py`
4. **Tests**: Add test cases to `tests/test_payment.py`

### Debugging

Enable debug output by adding logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or use print statements in development (remove for production).

## Troubleshooting

### Transaction Failures

1. Check ePort device status via STATUS command
2. Verify authorization amount matches expected sale amount
3. Check transaction result format (CRC, fields, separators)
4. Review ePort device logs (if available)

### Hardware Problems

1. Test GPIO pins independently
2. Verify flowmeter calibration
3. Check motor operation
4. Test button inputs

### Communication Errors

1. Verify serial port configuration
2. Check cable/connections
3. Test with serial terminal (minicom, screen)
4. Review protocol timing requirements

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]

## Support

For issues or questions, refer to:
- **Setup Guide**: `SETUP.md` - Installation and configuration
- **Testing Guide**: `TESTING.md` - Running and understanding tests
- **Protocol Documentation**: `../docs/Serial ePort Protocol -Rev 18.pdf` (if available)
