# Testing Guide

Quick guide to running tests for the vending machine controller.

---

## Test Suites

We have **two test suites** (32 tests total):

### 1. Payment Protocol Tests (`test_payment.py`)
**7 tests** - ePort credit card communication

- CRC16 checksum calculation
- Status, reset, authorization commands
- Transaction result
- Transaction ID retrieval

### 2. Multi-Product System Tests (`test_multi_product.py`)
**25 tests** - Product management and transactions

- **TestProduct** (5 tests) - Product validation, pricing
- **TestProductManager** (11 tests) - Config loading, duplicate detection
- **TestTransactionTracker** (9 tests) - Item tracking, totals, summaries

---

## Running Tests

### Run All Tests (Recommended)

```bash
# Payment protocol tests (7 tests)
python3 -m ePort.tests.test_payment

# Multi-product system tests (25 tests)
python3 -m ePort.tests.test_multi_product
```

### Expected Output

**Payment Tests:**
```
============================================================
Testing ePort Payment Protocol
============================================================
Results: 7 passed, 0 failed
============================================================
```

**Multi-Product Tests:**
```
============================================================
Testing Multi-Product System
============================================================
Results: 25 tests, 0 failures, 0 errors
============================================================
```

---

## What's Tested

### Payment Protocol
- **CRC16 calculation** - Data integrity for serial communication
- **Command formatting** - Status, reset, authorization, transaction result
- **Response parsing** - Transaction IDs, status codes
- **Error handling** - Invalid responses

### Multi-Product System
- **Product validation** - Prices, pins, calibration values
- **Config loading** - JSON parsing, duplicate detection
- **Transaction tracking** - Item lists, running totals, summaries
- **Price calculations** - Rounding, multi-item totals

---

## What's NOT Tested

These require hardware or complex integration mocking:
- `MachineController` GPIO operations
- `main.py` orchestration logic
- Timeout behavior
- Product switching flow

**Test these manually on Raspberry Pi hardware.**

---

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'ePort'
```
**Fix:** Run from project root (directory containing `ePort/` folder)

### Wrong Python Version
```
SyntaxError: invalid syntax
```
**Fix:** Use Python 3.7+
```bash
python3 --version  # Should be 3.7.0 or higher
```

### Tests Fail
1. Read error message carefully
2. Check which test failed
3. Look at the code being tested
4. Fix issue and re-run

---

## Adding New Tests

**When creating new test files:**

1. Create: `ePort/tests/test_[feature].py`
2. Update: `.github/workflows/pr-tests.yml`
3. Add test run command to CI/CD
4. Verify in GitHub Actions

See `.cursorrules` for detailed requirements.

---

## CI/CD Integration

Tests run automatically on every PR via GitHub Actions:
- Python 3.7 environment (matches Raspberry Pi)
- Both test suites must pass
- Syntax checks on all source files

See `.github/workflows/pr-tests.yml` for configuration.

---

**All 32 tests passing = Code ready for deployment** ✅
