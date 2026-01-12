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


def test_request_authorization():
    """Test AUTH_REQ command (command 21) for authorization request"""
    mock_serial = MockSerial()
    protocol = EPortProtocol(mock_serial)
    
    # Test requesting authorization for $20.00 (2000 cents)
    protocol.request_authorization(2000)
    
    # Check that command was written to serial
    assert len(mock_serial.write_buffer) > 0, "No data written to serial"
    
    # Verify command format: should start with "21" (0x32, 0x31) + RS (0x1E)
    command_bytes = bytes(mock_serial.write_buffer)
    assert command_bytes[0] == 0x32, "Command should start with '2' (0x32)"
    assert command_bytes[1] == 0x31, "Command should have '1' (0x31) as second byte"
    assert command_bytes[2] == RS, "Command should have RS (0x1E) as third byte"
    
    # Verify amount "2000" is in the command
    assert b'2000' in command_bytes, "Command should contain amount '2000'"
    
    # Verify command ends with CR (0x0D)
    assert command_bytes[-1] == CR, "Command should end with CR (0x0D)"
    
    print(f"✓ Authorization request command sent: ${2000 / 100:.2f}")
    print(f"✓ Command bytes written: {len(mock_serial.write_buffer)} bytes")
    print("✓ Request authorization test passed!")
    
    return True


def test_get_transaction_id():
    """Test get_transaction_id command (command 13)"""
    mock_serial = MockSerial()
    protocol = EPortProtocol(mock_serial)
    
    # Simulate a transaction ID response: "17" + RS + "12345678" + CR
    # Format: 17RSTransaction_IDCR
    transaction_id = "12345678"
    response = b'17' + bytes([RS]) + transaction_id.encode('ascii') + bytes([CR])
    mock_serial.read_buffer.extend(response)
    
    # Call get_transaction_id - it sends command 13, then status command
    # We need to set up the status response after command 13 is sent
    # Actually, get_transaction_id calls status() which sends '1' + CR
    # So we need to set up response for status command
    mock_serial.responses[b'1\r'] = response
    
    result = protocol.get_transaction_id()
    
    # Verify transaction ID was parsed correctly
    assert result == transaction_id, f"Expected transaction ID '{transaction_id}', got '{result}'"
    
    print(f"✓ Transaction ID retrieved: {result}")
    print("✓ Get transaction ID test passed!")
    
    return True


def test_get_transaction_id_no_response():
    """Test get_transaction_id when response doesn't match expected format"""
    mock_serial = MockSerial()
    protocol = EPortProtocol(mock_serial)
    
    # Set up a status response that doesn't match transaction ID format (not starting with "17")
    mock_serial.responses[b'1\r'] = b'9\r'  # Some other status code
    
    result = protocol.get_transaction_id()
    
    # Should return None when response doesn't match expected format
    assert result is None, "Should return None when response doesn't match transaction ID format"
    
    print("✓ Get transaction ID returns None for invalid response")
    print("✓ Get transaction ID (no response) test passed!")
    
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
        ("Request Authorization", test_request_authorization),
        ("Transaction Result Command", test_transaction_result_command),
        ("Get Transaction ID", test_get_transaction_id),
        ("Get Transaction ID (No Response)", test_get_transaction_id_no_response),
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
