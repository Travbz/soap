"""
ePort payment protocol handler
Handles all communication with the ePort card reader device
"""

import time
from typing import Optional
from ..config import CRC_TABLE, RS, GS, CR


class EPortProtocol:
    """Handles ePort serial protocol communication and CRC calculation"""
    
    def __init__(self, serial_connection):
        """
        Initialize ePort protocol handler
        
        Args:
            serial_connection: Serial connection object (real or mock)
        """
        self.ser = serial_connection
    
    @staticmethod
    def calculate_crc16(data: bytearray) -> int:
        """
        Calculate CRC16 using the algorithm from Serial ePort Protocol Appendix B.
        CRC is computed from the first byte including all control characters.
        
        Args:
            data: Bytearray to calculate CRC for
            
        Returns:
            16-bit CRC value
        """
        new_crc = 0xFFFF
        for byte in data:
            new_crc = ((new_crc << 8) ^ CRC_TABLE[(new_crc >> 8) ^ byte]) & 0xFFFF
        return new_crc
    
    def status(self) -> bytes:
        """Send STATUS command (command 1) and return response"""
        command = bytearray([0x31, CR])  # Command 1
        self.ser.write(command)
        time.sleep(0.5)
        return self.ser.readline().strip()
    
    def reset(self):
        """Send RESET command (command 3)"""
        command = bytearray([0x33, CR])
        self.ser.write(command)
        time.sleep(0.5)
    
    def request_authorization(self, amount_cents: int):
        """
        Send AUTH_REQ command (command 21) to authorize a credit card
        
        Args:
            amount_cents: Authorization amount in cents (e.g., 2000 = $20.00)
        """
        # Build payload: 21RS<amount>
        payload = bytearray([0x32, 0x31, RS])
        payload.extend(str(amount_cents).encode('ascii'))
        
        # Calculate CRC and build command
        crc = self.calculate_crc16(payload)
        command = bytearray(payload)
        command.append((crc >> 8) & 0xFF)
        command.append(crc & 0xFF)
        command.append(CR)
        
        self.ser.write(command)
        time.sleep(0.5)
    
    def send_transaction_result(self, quantity: int, price_cents: int, 
                                item_id: str, description: str) -> bool:
        """
        Send TRANSACTION_RESULT command (command 22) to complete a sale
        
        Args:
            quantity: Number of items sold (typically 1)
            price_cents: Price in cents
            item_id: Item identifier (0-5 digits as string)
            description: Item description (up to 30 bytes)
            
        Returns:
            True if command sent successfully
        """
        # Format: 22RSLINE-ITEMSRSITEM-QUANTITYRSITEM-PRICERSITEM-IDRSITEM-DESCRIPTIONGSCrcCR
        line_items = "1"
        
        # Build payload (without CRC and CR)
        payload = bytearray()
        payload.extend(b"22")  # Command 22
        payload.append(RS)
        payload.extend(line_items.encode('ascii'))
        payload.append(RS)
        payload.extend(str(quantity).encode('ascii'))
        payload.append(RS)
        payload.extend(str(price_cents).encode('ascii'))
        payload.append(RS)
        payload.extend(item_id.encode('ascii'))
        payload.append(RS)
        payload.extend(description[:30].encode('ascii'))
        payload.append(GS)
        
        # Calculate CRC
        crc = self.calculate_crc16(payload)
        
        # Build final command
        command = bytearray(payload)
        command.append((crc >> 8) & 0xFF)  # High byte
        command.append(crc & 0xFF)         # Low byte
        command.append(CR)
        
        self.ser.write(command)
        time.sleep(0.5)
        return True
    
    def get_transaction_id(self) -> Optional[str]:
        """
        Request transaction ID (command 13)
        
        Returns:
            Transaction ID as string, or None if not available
        """
        command = bytearray([0x31, 0x33, CR])  # Command 13
        self.ser.write(command)
        time.sleep(0.5)
        
        # Get response via STATUS command
        response = self.status()
        # Response format: 17RSTransaction_IDCR
        if response.startswith(b'17'):
            parts = response.split(bytes([RS]))
            if len(parts) >= 2:
                return parts[1].decode('ascii').strip()
        return None
