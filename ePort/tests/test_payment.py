"""
Test payment protocol with mocks
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ePort.src.payment import EPortProtocol
from ePort.tests.mocks import MockSerial
from ePort.config import RS, GS, CR


def test_crc_calculation():
    """Test CRC16 calculation matches expected values"""
    # Example from PDF: AUTH_REQ for $350 (21RS350) should give CRC E558
    # Command: 32 31 1E 33 35 30 E5 58 0D
    payload = bytearray([0x32, 0x31, RS, 0x33, 0x35, 0x30])
    crc = EPortProtocol.calculate_crc16(payload)
    
    # Expected CRC from PDF example
    expected_crc = 0xE558
    print(f"CRC Test: Calculated={crc:04X}, Expected={expected_crc:04X}")
    
    assert crc == expected_crc, f"CRC mismatch! Got {crc:04X}, expected {expected_crc:04X}"
    print("✓ CRC calculation test passed!")
    return True


def test_transaction_result_command():
    """Test TRANSACTION_RESULT command construction"""
    mock_serial = MockSerial()
    protocol = EPortProtocol(mock_serial)
    
    # Test sending transaction result
    success = protocol.send_transaction_result(
        quantity=1,
        price_cents=150,  # $1.50
        item_id="1",
        description="oz hand wash"
    )
    
    assert success, "Transaction result command failed"
    print("✓ Transaction result command test passed!")
    
    # Check that data was written
    assert len(mock_serial.write_buffer) > 0, "No data written to serial"
    print(f"✓ Command bytes written: {len(mock_serial.write_buffer)} bytes")
    
    return True


def test_status_command():
    """Test STATUS command"""
    mock_serial = MockSerial()
    mock_serial._simulate_disabled_state()
    protocol = EPortProtocol(mock_serial)
    
    response = protocol.status()
    print(f"✓ Status response: {response}")
    
    # Status strips the response, so compare without CR
    assert response == b'6', f"Unexpected status response: {response}"
    print("✓ Status command test passed!")
    
    return True


def test_reset_command():
    """Test RESET command"""
    mock_serial = MockSerial()
    protocol = EPortProtocol(mock_serial)
    
    protocol.reset()
    
    # Check that reset command was written
    assert len(mock_serial.write_buffer) > 0, "No data written to serial"
    print("✓ Reset command test passed!")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing ePort Payment Protocol")
    print("=" * 60)
    print()
    
    tests = [
        ("CRC Calculation", test_crc_calculation),
        ("Status Command", test_status_command),
        ("Reset Command", test_reset_command),
        ("Transaction Result Command", test_transaction_result_command),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}...")
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"✗ FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"✗ ERROR in {test_name}: {e}")
            failed += 1
            print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
