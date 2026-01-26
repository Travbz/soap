# Vending Machine Controller

A modular Python application for controlling a soap vending machine with integrated credit card payment processing via ePort Telemeter device.

## Overview

This system controls a vending machine that dispenses liquid soap by weight. It integrates with an ePort Telemeter card reader for credit card transactions using the Serial ePort Protocol. The application is designed to run continuously on a Raspberry Pi, monitoring for customer interactions and processing payments.

## Architecture

### Directory Structure

```
ePort/
├── config/              # Configuration constants
│   ├── __init__.py      # CRC table, protocol constants, hardware pins, timing values
│   └── products.json    # Product definitions (name, price, GPIO pins, calibration)
├── src/                 # Core application code
│   ├── machine.py       # MachineController - GPIO, motors, sensors, dispensing logic
│   ├── payment.py       # EPortProtocol - ePort communication and CRC calculation
│   ├── product.py       # Product - Single product representation
│   ├── product_manager.py  # ProductManager - Load and validate products from JSON
│   └── transaction_tracker.py  # TransactionTracker - Track items in current transaction
├── tests/               # Testing infrastructure
│   ├── mocks.py         # MockGPIO and MockSerial for testing without hardware
│   ├── test_payment.py  # Unit tests for payment protocol (7 tests)
│   └── test_multi_product.py  # Unit tests for product system (25 tests)
├── documentation/       # Project documentation
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
- **Motor Control**: Controls dispensing motor per product
- **Button Monitoring**: Handles product selection and completion buttons

Key methods:
- `start_dispensing()`: Initializes dispensing mode with callbacks
- `select_product()`: Sets active product and configures flowmeter
- `control_motor()`: Turns motor on/off for specific product
- `get_pressed_product_button()`: Detects which product button is pressed
- `reset()`: Resets dispense counters and turns off all motors

#### 3. **Product System (`src/product.py`, `src/product_manager.py`)**

**Product class** represents a single product:
- Validates configuration (positive prices, unique pins)
- Calculates price based on quantity
- Stores GPIO pin assignments and calibration

**ProductManager class** manages product lifecycle:
- Loads products from `config/products.json`
- Validates no duplicate IDs or GPIO pins
- Provides lookup by ID or button pin

Key methods:
- `load_products()`: Load and validate products from JSON
- `get_product()`: Retrieve product by ID
- `get_product_by_button_pin()`: Find product by button pin
- `list_products()`: Get all products

#### 4. **Transaction Tracker (`src/transaction_tracker.py`)**

The `TransactionTracker` class tracks items in a single transaction:

- Accumulates multiple products dispensed in one card authorization
- Calculates total price across all items
- Generates itemized summaries for customer and ePort
- Uses Decimal for precise financial calculations

Key methods:
- `add_item()`: Record product dispensed with quantity and price
- `get_total_cents()`: Get total price in cents for ePort
- `get_summary()`: Generate itemized receipt
- `get_eport_description_multiple_items()`: Format description for ePort (30 byte limit)
- `reset()`: Clear transaction for next customer

#### 5. **Configuration (`config/__init__.py`, `config/products.json`)**

**config/__init__.py** - System-wide constants:
- **CRC Table**: Complete lookup table for CRC16 calculation
- **Protocol Constants**: RS, GS, CR, ACK, NAK separators
- **Timing Values**: All delays and timeouts (ePort commands, debouncing, session limits)
- **Hardware Pins**: Shared pins (done button)
- **Serial Settings**: Port, baudrate, timeout
- **Transaction Limits**: Max items, session timeouts

**config/products.json** - Product definitions:
- Per-product GPIO pins (motor, flowmeter, button)
- Pricing and calibration
- Product metadata (name, description, unit)

### Data Flow

1. **Initialization**:
   - Load products from `config/products.json`
   - Validate product configuration (no duplicate pins/IDs)
   - Initialize GPIO and serial port
   - Set up product button event detection

2. **Status Polling**: Continuously polls ePort device status

3. **Customer Interaction**:
   - Customer swipes card → Authorization requested for $20.00
   - If approved → Dispensing mode enabled
   - Customer selects product (presses product button)
   - Motor activates for selected product
   - Flowmeter tracks quantity dispensed
   - Item added to transaction tracker
   - Customer can select additional products
   - Customer presses done → Transaction result sent to ePort with total

4. **Transaction Completion**:
   - Transaction ID retrieved
   - Itemized summary displayed
   - System resets for next customer

5. **Timeout Protection**:
   - Inactivity timeout: 60s with no button press → auto-complete
   - Max session: 5 minutes → auto-complete
   - Warning displayed 15s before timeout

## Multi-Product Support

The system supports multiple products in a single transaction:

- Customer can dispense multiple products before pressing done
- Each product has independent GPIO pins (motor, flowmeter, button)
- Transaction tracker accumulates items and calculates total
- Single card authorization covers all products dispensed

**Configuration**: Edit `config/products.json` to add products

**Validation**: System prevents duplicate GPIO pins and product IDs

**Limits**: Max 10 items per transaction (configurable)

## Future Enhancements

See PRD documents in `documentation/` for planned features:

- **Inventory Tracking** (`PRD-InventoryTracking.md`): SQLite database, low stock alerts, usage analytics
- **Customer Display** (`PRD-CustomerDisplay.md`): Visual guidance with graphics/video
- **Centralized Logging** (`PRD-CentralizedLogging.md`): Remote monitoring, fleet management, SMS alerts

## Protocol Reference

This implementation follows the **Serial ePort Protocol - Revision 18** specification.

Key protocol details:
- **Baudrate**: 9600 8-N-1 (no flow control)
- **CRC Algorithm**: CRC16 with lookup table
- **Command Format**: ASCII commands with CRC and CR termination
- **Status Polling**: Continuous polling during idle

For detailed protocol documentation, see `ePort-Protocol-Reference.md`

## Development

### Code Structure

The codebase follows a modular architecture:

- **Separation of Concerns**: Payment, machine, product logic in separate modules
- **Dependency Injection**: Hardware interfaces passed as parameters (enables testing)
- **Configuration Centralization**: All settings in `config/`
- **Testability**: Mocks enable testing without hardware

### Adding Features

1. **New Protocol Commands**: Add methods to `EPortProtocol` class
2. **New Hardware**: Extend `MachineController` class
3. **Configuration Changes**: Update `config/__init__.py` or `config/products.json`
4. **Tests**: Add test cases and update CI/CD workflow

### Debugging

Logging is configured in `main.py`:
- Customer output: `print()` statements (no timestamps)
- System logs: `logger.info()`, `logger.debug()`, `logger.error()`

View logs:
```bash
sudo journalctl -u vending-machine -f
```

## Support

For issues or questions, refer to:
- **Setup Guide**: `SETUP.md` - Installation and configuration
- **Testing Guide**: `TESTING.md` - Running and understanding tests
- **SDLC Guide**: `SDLC.md` - Development workflow and CI/CD
- **Protocol Reference**: `ePort-Protocol-Reference.md` - ePort communication details
