# Vending Machine Controller

**Multi-Product Raspberry Pi Vending Machine with Credit Card Payment Processing**

A production-ready vending machine controller that handles credit card payments via ePort serial protocol and manages multiple products with different pricing, motors, and flowmeters.

---

## 🎯 Features

### ✅ Implemented

- **Multi-Product Support**: Configure unlimited products via JSON
- **Credit Card Processing**: ePort serial protocol integration (9600 8-N-1)
- **Customer Display**: Real-time web-based display with live counters and receipts
- **Real-Time Dispensing**: GPIO-controlled motors with flowmeter feedback
- **Transaction Tracking**: Itemized receipts for multiple products per transaction
- **Auto-Setup**: One-command installation with dependency detection
- **Timeout Protection**: Auto-complete abandoned sessions (60s inactivity, 5min max)
- **Safety Limits**: Max transaction price, item count limits, validation
- **Comprehensive Testing**: 32 unit tests, all passing
- **Production Ready**: Error handling, logging, retry logic

### 🚧 Planned (Future Phases)

- **Inventory Tracking**: SQLite-based inventory with low-stock alerts (PRD complete)
- **Centralized Logging**: Remote monitoring and analytics (PRD complete)
- **Remote Notifications**: ePort cellular for alerts and diagnostics (documented)

---

## 📁 Project Structure

```
ePort/
├── main.py                     # Entry point - orchestrates payment & dispensing
├── requirements.txt            # Python dependencies
├── vending-machine.service     # systemd service for auto-start
│
├── config/
│   ├── __init__.py            # All configuration constants
│   └── products.json          # Product definitions (pricing, pins, calibration)
│
├── src/
│   ├── payment.py             # EPortProtocol - credit card communication
│   ├── machine.py             # MachineController - GPIO/hardware control
│   ├── product.py             # Product - data class for product config
│   ├── product_manager.py     # ProductManager - loads/manages products
│   └── transaction_tracker.py # TransactionTracker - tracks items & totals
│
├── scripts/
│   └── setup.sh               # Automated setup script
│
├── display/
│   ├── templates/             # HTML templates for customer display
│   └── static/                # CSS and JavaScript for display
│
├── tests/
│   ├── mocks.py               # Mock GPIO & serial for testing
│   ├── test_payment.py        # ePort protocol tests (7 tests)
│   ├── test_multi_product.py  # Multi-product system tests (25 tests)
│   ├── test_display.py        # Display system test/demo
│   └── setup_dev.sh           # Dev environment setup
│
└── documentation/
    ├── ARCHITECTURE.md         # System architecture & design
    ├── SETUP.md                # Installation & deployment guide
    ├── TESTING.md              # Testing strategy & approach
    ├── SDLC.md                 # Development workflow & CI/CD
    ├── PRD-MultiProduct.md     # Multi-product feature requirements
    ├── PRD-CustomerDisplay.md  # Display system requirements
    ├── PRD-InventoryTracking.md # Inventory management requirements
    ├── PRD-CentralizedLogging.md # Remote logging requirements
    ├── ePort-Protocol-Reference.md # ePort serial protocol details
    └── ePort-Notifications.md  # ePort cellular notifications guide
```

---

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi (tested on Pi 3/4)
- Python 3.7+
- ePort credit card reader (serial connection)
- HDMI display (for customer interface)
- GPIO-connected hardware (motors, flowmeters, buttons)

### Installation

**One command - everything else is automatic:**

```bash
# Clone and run
git clone git@github.com:Travbz/soap.git
cd soap
python3 -m ePort.main
```

The system auto-detects if setup is needed and runs it automatically. After setup completes, just reboot.

### View Display Demo (Development)

```bash
# Setup dev environment
cd ePort/tests
./setup_dev.sh
source .venv/bin/activate

# Run display test
python3 -m ePort.tests.test_display

# Open browser to http://localhost:5000
```

### Configuration

Edit `ePort/config/products.json`:

```json
{
  "products": [
    {
      "id": "soap_hand",
      "name": "Hand Soap",
      "description": "Gentle hand wash soap",
      "price_per_unit": 0.15,
      "unit": "oz",
      "motor_pin": 17,
      "flowmeter_pin": 24,
      "button_pin": 4,
      "pulses_per_unit": 5.4
    },
    {
      "id": "soap_dish",
      "name": "Dish Soap",
      "description": "Powerful dish cleaning soap",
      "price_per_unit": 0.12,
      "unit": "oz",
      "motor_pin": 18,
      "flowmeter_pin": 25,
      "button_pin": 23,
      "pulses_per_unit": 5.2
    }
  ]
}
```

---

## 🏗️ Core Components

### 1. Payment Processing (`ePort/src/payment.py`)

**EPortProtocol Class** - Handles credit card transactions via serial protocol

**Key Methods:**
- `status()` - Check ePort device status
- `reset()` - Reset device for new transaction
- `request_authorization(amount_cents)` - Request card authorization
- `send_transaction_result(price, quantity, description)` - Complete transaction
- `get_transaction_id()` - Retrieve transaction ID for records

**Protocol Details:**
- Serial: 9600 baud, 8-N-1
- CRC16 checksums for data integrity
- Control characters: RS, GS, CR, ACK, NAK
- Master-slave communication (Pi is master)

---

### 2. Hardware Control (`ePort/src/machine.py`)

**MachineController Class** - Manages GPIO hardware for all products

**Key Methods:**
- `select_product(product)` - Switch active product
- `start_dispensing(callbacks)` - Enable dispensing mode
- `control_motor(state)` - Turn motor on/off
- `get_pressed_product_button()` - Detect which button is pressed
- `setup_flowmeter_for_product(product)` - Configure flowmeter interrupts
- `reset()` - Clean up GPIO state for next customer

**Hardware Support:**
- Multiple motors (one per product)
- Multiple flowmeters (pulse counting)
- Multiple product selection buttons
- Single "done" button (shared)
- GPIO interrupts for real-time response

---

### 3. Product Management (`ePort/src/product_manager.py`)

**ProductManager Class** - Loads and validates product configurations

**Key Methods:**
- `load_products()` - Parse JSON config, validate pins/prices
- `get_product(product_id)` - Lookup product by ID
- `get_product_by_button_pin(pin)` - Find product from button press
- `list_products()` - Get all available products

**Validation:**
- No duplicate GPIO pins (motor, flowmeter, button)
- No duplicate product IDs
- Positive prices and calibration values
- Required fields present

---

### 4. Transaction Tracking (`ePort/src/transaction_tracker.py`)

**TransactionTracker Class** - Records items dispensed in current transaction

**Key Methods:**
- `add_item(product_id, name, quantity, unit, price)` - Record dispensed item
- `get_total()` - Calculate total price (dollars)
- `get_total_cents()` - Calculate total price (cents for ePort)
- `get_summary()` - Generate itemized receipt
- `get_eport_description()` - Compact description (30 byte limit)
- `reset()` - Clear for next transaction

**Features:**
- Tracks multiple products per transaction
- Calculates running totals
- Generates customer-facing summaries
- Handles price rounding correctly

---

### 5. Main Controller (`ePort/main.py`)

**Orchestration** - Coordinates all components

**Flow:**
1. Initialize ProductManager, GPIO, Serial, Payment, Machine
2. Main loop: Poll ePort status
3. On authorization (status `9`): Enter dispensing mode
4. Dispensing loop:
   - Monitor product buttons
   - Switch products as needed
   - Control motors based on button state
   - Track flowmeter pulses
   - Check for timeouts (inactivity, max session)
   - Complete on "done" button or timeout
5. Send itemized transaction result to ePort
6. Reset machine for next customer

**Timeout Protection:**
- **Inactivity**: 60 seconds without button press → auto-complete
- **Warning**: Display warning at 45 seconds
- **Max Session**: 5 minutes total → force complete
- **Empty Transaction**: Cancel if nothing dispensed

---

## 🔧 Configuration Reference

### Key Constants (`ePort/config/__init__.py`)

**Serial/ePort:**
```python
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 9600
AUTH_AMOUNT_CENTS = 2000  # Pre-authorize $20.00
```

**GPIO Pins:**
```python
DONE_BUTTON_PIN = 27  # Shared done button
# Product-specific pins in products.json
```

**Safety Limits:**
```python
MAX_TRANSACTION_PRICE = 1000.0  # Max $1000 per transaction
MAX_ITEMS_PER_TRANSACTION = 10  # Max 10 different products
```

**Timeouts:**
```python
DISPENSING_INACTIVITY_TIMEOUT = 60   # 60s no activity → auto-complete
DISPENSING_MAX_SESSION_TIME = 300    # 5min max session
INACTIVITY_WARNING_TIME = 45         # Warn at 45s
PRODUCT_SWITCH_DELAY = 0.5           # 0.5s between product switches
```

**Timing:**
```python
EPORT_COMMAND_DELAY = 0.5            # Wait after ePort commands
MOTOR_CONTROL_LOOP_DELAY = 0.1       # Main loop sleep
MOTOR_OFF_DEBOUNCE_DELAY = 0.7       # Delay before motor off
DONE_BUTTON_HARDWARE_DEBOUNCE_MS = 500  # Button debounce
```

---

## 🧪 Testing

### Run All Tests

```bash
# Payment protocol tests (7 tests)
python3 -m ePort.tests.test_payment

# Multi-product system tests (25 tests)
python3 -m ePort.tests.test_multi_product
```

### Test Coverage

**Payment Protocol:**
- CRC16 calculation
- Status command
- Reset command
- Authorization request
- Transaction result
- Transaction ID retrieval

**Multi-Product System:**
- Product creation & validation
- ProductManager loading & validation
- Duplicate pin detection
- TransactionTracker calculations
- Price rounding
- Itemized summaries

---

## 📊 User Flow

### Customer Transaction

```
1. Customer approaches machine
   ↓
2. Swipe credit card
   ↓
3. ePort authorizes $20.00
   ↓
4. Machine displays: "SELECT A PRODUCT TO BEGIN"
   • Hand Soap ($0.15/oz)
   • Dish Soap ($0.12/oz)
   ↓
5. Customer presses "Hand Soap" button
   → Machine displays: "Now dispensing: Hand Soap"
   → Customer holds button to dispense
   → Flowmeter tracks ounces in real-time
   ↓
6. Customer releases button
   → Motor stops
   ↓
7. Customer presses "Dish Soap" button
   → Previous product (Hand Soap) recorded
   → Machine displays: "Now dispensing: Dish Soap"
   → Customer holds button to dispense
   ↓
8. Customer presses "DONE" button
   ↓
9. Machine displays itemized receipt:
   ────────────────────────────────────
   TRANSACTION SUMMARY
   ────────────────────────────────────
   Hand Soap: 2.50 oz - $0.38
   Dish Soap: 3.20 oz - $0.38
   ────────────────────────────────────
   TOTAL: $0.76
   ────────────────────────────────────
   ↓
10. ePort charges card $0.76
    ↓
11. Machine displays: "Thank you! Machine ready for next customer"
```

### Timeout Scenarios

**Scenario 1: Customer walks away (no dispensing)**
- After 60 seconds: Cancel transaction, no charge

**Scenario 2: Customer walks away (after dispensing)**
- At 45 seconds: Display warning
- At 60 seconds: Auto-complete, charge for what was dispensed

**Scenario 3: Customer takes too long**
- At 5 minutes: Force complete transaction

---

## 🔐 Security & Safety

### Payment Security
- No card data stored locally
- ePort handles all PCI compliance
- Transaction IDs logged for audit trail

### Hardware Safety
- Max transaction price limit ($1000)
- Max items per transaction (10)
- Motor error detection & retry
- GPIO cleanup on exit
- Timeout protection prevents blocking

### Data Validation
- Product config validation on startup
- Duplicate pin detection
- Positive price/calibration enforcement
- CRC16 checksums on serial data

---

## 📈 Monitoring & Logs

### Log Levels

```python
logger.debug()    # Flowmeter pulses, detailed diagnostics
logger.info()     # Normal operations, status changes
logger.warning()  # Recoverable errors, timeouts
logger.error()    # Errors needing attention
logger.critical() # Fatal errors causing shutdown
```

### Customer Output

Clean output without timestamps (via `print()`):
```
SELECT A PRODUCT TO BEGIN
  • Hand Soap ($0.15/oz)
  • Dish Soap ($0.12/oz)

→ Now dispensing: Hand Soap

⚠️  WARNING: 15 seconds until auto-complete
   Press DONE or select a product to continue

TRANSACTION SUMMARY
────────────────────────────────────
Hand Soap: 2.50 oz - $0.38
────────────────────────────────────
TOTAL: $0.38
```

---

## 🚀 Deployment

### systemd Service

```bash
# Copy service file
sudo cp ePort/vending-machine.service /etc/systemd/system/

# Enable auto-start on boot
sudo systemctl enable vending-machine

# Start service
sudo systemctl start vending-machine

# Check status
sudo systemctl status vending-machine

# View logs
sudo journalctl -u vending-machine -f
```

---

## 🛠️ Development

### Workflow

1. Create feature branch: `git checkout -b feature/name`
2. Make changes following `.cursorrules`
3. Run tests: `python3 -m ePort.tests.test_*`
4. Commit with conventional commits: `git commit -m "feat: description"`
5. Push and create PR
6. Tests run automatically via GitHub Actions
7. Merge to `main` → Automated release created

### Conventional Commits

```bash
feat:     # New feature (minor version bump)
fix:      # Bug fix (patch version bump)
refactor: # Code refactoring (patch version bump)
docs:     # Documentation only (patch version bump)
test:     # Test changes (no release)
chore:    # Maintenance (patch version bump)
```

### GitHub Actions

- **PR Tests** (`.github/workflows/pr-tests.yml`): Run on PR open/update
- **Release** (`.github/workflows/release.yml`): Auto-release on merge to main

---

## 📚 Documentation

### Core Docs
- **[ARCHITECTURE.md](ePort/documentation/ARCHITECTURE.md)** - System design & components
- **[SETUP.md](ePort/documentation/SETUP.md)** - Installation & deployment
- **[TESTING.md](ePort/documentation/TESTING.md)** - Testing strategy
- **[SDLC.md](ePort/documentation/SDLC.md)** - Development workflow

### PRDs (Product Requirements)
- **[PRD-MultiProduct.md](ePort/documentation/PRD-MultiProduct.md)** - Multi-product system
- **[PRD-InventoryTracking.md](ePort/documentation/PRD-InventoryTracking.md)** - Inventory management
- **[PRD-CustomerDisplay.md](ePort/documentation/PRD-CustomerDisplay.md)** - Visual guidance
- **[PRD-CentralizedLogging.md](ePort/documentation/PRD-CentralizedLogging.md)** - Remote monitoring

### Technical References
- **[ePort-Protocol-Reference.md](ePort/documentation/ePort-Protocol-Reference.md)** - Serial protocol details
- **[ePort-Notifications.md](ePort/documentation/ePort-Notifications.md)** - Cellular notifications

---

## 🐛 Troubleshooting

### Common Issues

**"Serial port not found"**
```bash
# Check USB devices
ls -l /dev/ttyUSB*

# Add user to dialout group
sudo usermod -a -G dialout $USER
```

**"GPIO already in use"**
```bash
# Kill existing process
sudo pkill -f ePort.main

# Clean up GPIO
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.cleanup()"
```

**"Product config invalid"**
- Check `products.json` for duplicate pins
- Verify all required fields present
- Ensure positive prices and calibration values

**"Tests failing"**
- Ensure Python 3.7+ installed
- Check `pyserial` installed: `pip3 install pyserial`
- Run from project root: `cd /path/to/soap`

---

## 📝 License

[Add your license here]

---

## 👥 Contributing

1. Read `.cursorrules` for coding standards
2. Follow conventional commit format
3. Add tests for new features
4. Update documentation
5. Create PR with clear description

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Travbz/soap/issues)
- **Docs**: See `ePort/documentation/` folder
- **Tests**: Run `python3 -m ePort.tests.test_*` for examples

---

**Built with ❤️ for reliable, production-ready vending machine control**
