"""
Mock classes for testing without hardware
"""

import time
from typing import Optional


class MockGPIO:
    """Mock GPIO for testing without Raspberry Pi hardware"""
    
    BCM = 'BCM'
    IN = 'IN'
    OUT = 'OUT'
    PUD_UP = 'PUD_UP'
    RISING = 'RISING'
    FALLING = 'FALLING'
    LOW = 0
    HIGH = 1
    
    def __init__(self):
        self.pins = {}
        self.modes = {}
        self.event_callbacks = {}
        self.setup_calls = []
    
    def setmode(self, mode):
        """Set GPIO mode"""
        self.mode = mode
    
    def setup(self, pin, direction, pull_up_down=None):
        """Setup GPIO pin"""
        self.setup_calls.append((pin, direction, pull_up_down))
        self.pins[pin] = self.HIGH if direction == self.IN else self.LOW
    
    def input(self, pin):
        """Read GPIO pin"""
        return self.pins.get(pin, self.HIGH)
    
    def output(self, pin, value):
        """Write GPIO pin"""
        self.pins[pin] = value
    
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        """Add event detection (stored but not actually triggered)"""
        self.event_callbacks[pin] = {
            'edge': edge,
            'callback': callback,
            'bouncetime': bouncetime
        }
    
    def simulate_button_press(self, pin):
        """Simulate a button press for testing"""
        if pin in self.event_callbacks:
            cb_info = self.event_callbacks[pin]
            if cb_info['edge'] == self.FALLING:
                cb_info['callback'](pin)
    
    def simulate_flowmeter_pulse(self, pin):
        """Simulate a flowmeter pulse for testing"""
        if pin in self.event_callbacks:
            cb_info = self.event_callbacks[pin]
            if cb_info['edge'] == self.RISING:
                cb_info['callback'](pin)


class MockSerial:
    """Mock serial connection for testing without ePort device"""
    
    def __init__(self, port=None, baudrate=9600, timeout=1, **kwargs):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_buffer = bytearray()
        self.read_buffer = bytearray()
        self.responses = {
            b'1\r': b'0\r',  # STATUS -> OK (idle)
            b'3\r': b'\x06',  # RESET -> ACK
        }
        self._simulate_disabled_state()
    
    def _simulate_disabled_state(self):
        """Simulate ePort in disabled state"""
        self.responses[b'1\r'] = b'6\r'  # STATUS -> DISABLED
    
    def _simulate_enabled_state(self):
        """Simulate ePort in enabled state"""
        self.responses[b'1\r'] = b'0\r'  # STATUS -> OK
    
    def _simulate_waiting_for_swipe(self):
        """Simulate ePort waiting for card swipe"""
        self.responses[b'1\r'] = b'7\r'  # STATUS -> XPCTNG_SWIPE
    
    def _simulate_authorizing(self):
        """Simulate ePort authorizing"""
        self.responses[b'1\r'] = b'8\r'  # STATUS -> AUTHORIZING
    
    def _simulate_authorized(self, amount_cents=150, card_number="601100******000"):
        """Simulate successful authorization"""
        response = f"2{chr(0x1E)}{amount_cents}{chr(0x1E)}{card_number}".encode('ascii')
        # Add mock CRC (would need real calculation in full implementation)
        self.responses[b'1\r'] = response + b'\r'
    
    def _simulate_waiting_transaction_result(self):
        """Simulate ePort waiting for transaction result"""
        self.responses[b'1\r'] = b'9\r'  # STATUS -> XPCTNG_TRANS_RESULT
    
    def write(self, data: bytearray):
        """Write data to serial port (stored in buffer)"""
        self.write_buffer.extend(data)
        
        # Simulate responses for known commands (convert bytearray to bytes for comparison)
        data_bytes = bytes(data)
        if data_bytes in self.responses:
            self.read_buffer.extend(self.responses[data_bytes])
    
    def readline(self) -> bytes:
        """Read a line from serial port"""
        if b'\r' in self.read_buffer:
            idx = self.read_buffer.index(b'\r') + 1
            line = bytes(self.read_buffer[:idx])
            self.read_buffer = self.read_buffer[idx:]
            return line
        return b''
    
    def flush(self):
        """Flush buffers"""
        pass
    
    def close(self):
        """Close serial connection"""
        pass
