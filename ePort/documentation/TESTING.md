# Testing Guide

This directory contains tests for the vending machine controller code. Tests allow you to verify that the code works correctly **without needing actual hardware** (Raspberry Pi, GPIO pins, ePort device, etc.).

## What are Tests?

Tests are small programs that automatically check if your code works as expected. They:
- **Verify functionality** - Make sure code does what it's supposed to do
- **Catch bugs early** - Find problems before deploying to the actual machine
- **Run without hardware** - Test payment processing logic without a card reader
- **Provide confidence** - Know your code works before using it in production

## Prerequisites

Before running tests, you need Python 3.7 or higher installed on your computer.

### Check Python Version

Open a terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
python3 --version
```

You should see something like `Python 3.7.0` or higher. If not, install Python from [python.org](https://www.python.org/downloads/).

### Required Libraries

The tests use **mocks** (fake versions) of hardware, so you don't need to install GPIO or serial libraries for testing. However, if you want to use `pytest` (optional but recommended), install it:

```bash
pip3 install pytest
```

**Note**: The tests can run without `pytest` - they work with plain Python too!

## Setup Instructions

### Step 1: Navigate to Project Directory

Open a terminal and navigate to the project root directory:

```bash
cd /path/to/yfi-scanner
```

Replace `/path/to/yfi-scanner` with the actual path where you cloned/downloaded the project.

### Step 2: Verify Tests Can Run

Make sure you can import the test file:

```bash
python3 ePort/tests/test_payment.py --help
```

If you see output (or no error), you're ready to run tests!

## Running Tests

You have two options for running tests:

### Option 1: Run Directly (No Additional Setup)

Run the test file directly with Python:

```bash
python3 ePort/tests/test_payment.py
```

This will run all tests and show you the results.

**Example Output:**
```
============================================================
Testing ePort Payment Protocol
============================================================

Running: CRC Calculation...
CRC Test: Calculated=E558, Expected=E558
✓ CRC calculation test passed!

Running: Status Command...
✓ Status response: b'6'
✓ Status command test passed!

Running: Reset Command...
✓ Reset command test passed!

Running: Transaction Result Command...
✓ Transaction result command test passed!
✓ Command bytes written: 29 bytes

============================================================
Results: 4 passed, 0 failed
============================================================
```

### Option 2: Using pytest (Recommended)

If you installed `pytest`, you can run tests with more detailed output:

```bash
# Run all tests
pytest ePort/tests/ -v

# Run a specific test file
pytest ePort/tests/test_payment.py -v

# Run with more details
pytest ePort/tests/test_payment.py -vv
```

**Example Output:**
```
============================= test session starts =============================
platform darwin -- Python 3.12.9, pytest-7.4.4
collected 4 items

ePort/tests/test_payment.py::test_crc_calculation PASSED        [ 25%]
ePort/tests/test_payment.py::test_transaction_result_command PASSED [ 50%]
ePort/tests/test_payment.py::test_status_command PASSED         [ 75%]
ePort/tests/test_payment.py::test_reset_command PASSED          [100%]

======================== 4 passed in 1.55s =========================
```

## Understanding the Tests

The test suite includes the following tests:

### 1. CRC Calculation Test

**What it does:**
- Tests the CRC16 checksum calculation algorithm
- Verifies it matches the specification from the ePort Protocol PDF

**Why it matters:**
- CRC (Cyclic Redundancy Check) is used to verify data integrity
- **This was the bug that caused the original failure** - the CRC calculation was wrong
- If this test passes, your payment commands will work correctly

**What it checks:**
- Calculates CRC for the example from the PDF: AUTH_REQ for $3.50 (21RS350)
- Expected CRC: E558
- If calculated CRC matches expected, test passes ✓

### 2. Status Command Test

**What it does:**
- Tests communication with the ePort device using the STATUS command
- Uses a mock (fake) serial connection instead of real hardware

**Why it matters:**
- Status commands are sent repeatedly to check device state
- This is the "heartbeat" of the system

**What it checks:**
- Can send STATUS command (command 1)
- Can read the response correctly
- Response format matches protocol specification

### 3. Reset Command Test

**What it does:**
- Tests the RESET command (command 3)
- Verifies the command can be sent to the ePort device

**Why it matters:**
- Reset is used to clear device state and prepare for new transactions
- Must work correctly for the machine to function

**What it checks:**
- RESET command can be constructed and sent
- No errors occur during command transmission

### 4. Transaction Result Command Test

**What it does:**
- Tests the TRANSACTION_RESULT command (command 22)
- This is the **most complex command** - it includes CRC calculation
- Simulates completing a sale transaction

**Why it matters:**
- This command completes a sale after product is dispensed
- **This was the 7th command that was failing** in the original code
- Must include correct CRC or the payment processor will reject it

**What it checks:**
- Command format matches protocol specification
- All fields are correctly formatted (quantity, price, item ID, description)
- CRC is calculated and included correctly
- Command bytes are generated properly

## Test Results Explained

### Passing Tests ✓

When a test **passes**, it means:
- The code works correctly for that function
- The implementation matches the specification
- No bugs detected for that feature

**Good news:** All tests should pass! If they do, your code is ready to use.

### Failing Tests ✗

If a test **fails**, you'll see:
- An error message explaining what went wrong
- Which assertion failed
- Expected vs. actual values

**What to do:**
1. Read the error message carefully
2. Check which test failed
3. Look at the code being tested
4. Fix the issue and run tests again

### Common Issues

#### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'ePort'
```

**Solution:**
- Make sure you're running tests from the project root directory
- The project root should contain the `ePort/` folder

#### Syntax Errors

**Error:**
```
SyntaxError: invalid syntax
```

**Solution:**
- Check your Python version: `python3 --version`
- Make sure you're using Python 3.7 or higher
- Verify the test file wasn't accidentally modified

## What Tests DON'T Test

These tests use **mocks** (fake hardware), so they don't test:

- ❌ Actual GPIO pin operations (need real Raspberry Pi)
- ❌ Real serial communication with ePort device
- ❌ Physical motor control
- ❌ Actual button presses or sensor readings
- ❌ Hardware wiring or connections

**To test with real hardware:**
- Deploy the code to a Raspberry Pi
- Connect all hardware properly
- Test with actual card transactions (test mode)

## Understanding Mocks

**What are mocks?**
- Fake versions of hardware components
- Simulate real hardware behavior
- Allow testing without physical devices

**MockGPIO** (`tests/mocks.py`):
- Fake GPIO pins and operations
- Simulates button presses and motor control
- No real hardware needed

**MockSerial** (`tests/mocks.py`):
- Fake serial port connection
- Simulates ePort device responses
- No real card reader needed

**Why use mocks?**
- Test code logic without hardware
- Run tests on any computer
- Test edge cases safely
- Faster than hardware testing

## Running Tests During Development

### Before Making Changes

1. **Run tests first:**
   ```bash
   python3 ePort/tests/test_payment.py
   ```
2. **Verify all tests pass** - This is your baseline
3. **Make your changes** to the code
4. **Run tests again** - Make sure you didn't break anything

### After Making Changes

Always run tests after:
- Modifying payment protocol code
- Changing CRC calculation
- Updating command formats
- Fixing bugs

**Good practice:** Run tests frequently during development to catch bugs early!

## Troubleshooting

### Tests Won't Run

**Problem:** `python3: command not found`

**Solution:**
- Install Python 3 from [python.org](https://www.python.org/downloads/)
- Or try `python` instead of `python3` (Windows)
- Make sure Python is in your system PATH

### Import Errors

**Problem:** Can't import ePort modules

**Solution:**
- Make sure you're in the project root directory
- Check that `ePort/` folder exists
- Verify `ePort/__init__.py` exists

### Tests Fail But Code Looks Right

**Problem:** Tests fail but you think the code is correct

**Solution:**
- Read the error message carefully
- Check expected vs. actual values
- Verify you understand what the test is checking
- Look at the protocol specification if needed
- Ask for help if stuck!

## Next Steps

After tests pass:

1. ✅ **Code is verified** - Payment logic works correctly
2. 🚀 **Ready for deployment** - Can install on Raspberry Pi
3. 🔧 **Deploy to hardware** - Follow deployment guide
4. 🧪 **Test with real hardware** - Use test mode with real card reader

## Additional Resources

- **Protocol Documentation:** `../docs/Serial ePort Protocol -Rev 18.pdf`
- **Main README:** `../../README.md`
- **Deployment Guide:** `../deployment.md`

## Summary

- **Run tests:** `python3 ePort/tests/test_payment.py`
- **All tests should pass** before deploying code
- **Tests use mocks** - no hardware needed
- **CRC test is critical** - this was the original bug
- **Transaction Result test** - this was the failing command

If all tests pass, your code is ready! 🎉
