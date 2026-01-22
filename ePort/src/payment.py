"""
ePort payment protocol handler
Handles all communication with the ePort card reader device
"""

import time
from typing import Optional
from ..config import CRC_TABLE, RS, GS, CR, EPORT_COMMAND_DELAY


class EPortProtocol:
    """
    Handles ePort serial protocol communication and CRC calculation
    
    This class manages all communication with the ePort credit card reader device.
    The ePort uses a serial protocol (RS-232 over USB) with specific command formats.
    
    Key concepts:
    - Commands are sent as byte arrays with specific formats
    - Every command must include a CRC16 checksum for error detection
    - Commands end with CR (carriage return, 0x0D)
    - Fields are separated by RS (Record Separator, 0x1E) or GS (Group Separator, 0x1D)
    - Responses are read back from the serial port
    
    The ePort device handles communication with the payment processor and reports
    status codes back to indicate authorization results.
    """
    
    def __init__(self, serial_connection):
        """
        Initialize ePort protocol handler
        
        Args:
            serial_connection: Serial connection object (real pyserial.Serial or mock for testing)
                              This should already be opened and configured with the correct
                              baud rate, timeout, etc.
        """
        self.ser = serial_connection
    
    @staticmethod
    def calculate_crc16(data: bytearray) -> int:
        """
        Calculate CRC16 checksum using the algorithm from Serial ePort Protocol Appendix B.
        
        CRC (Cyclic Redundancy Check) is a way to detect errors in data transmission.
        The ePort device requires a CRC16 checksum at the end of every command. If the
        CRC is wrong, the device will reject the command.
        
        The algorithm uses a lookup table (CRC_TABLE) for efficiency. This is a standard
        CCITT CRC16 implementation specifically required by the ePort protocol.
        
        Args:
            data: Bytearray to calculate CRC for (the command data before CRC bytes)
            
        Returns:
            16-bit CRC value (0x0000 to 0xFFFF) that gets appended to the command
            
        Note:
            CRC is computed from the first byte including all control characters (RS, GS, etc.)
        """
        # Initialize CRC to 0xFFFF (standard starting value for CRC16)
        new_crc = 0xFFFF
        
        # Process each byte in the data using the lookup table algorithm
        for byte in data:
            # This is the CRC16-CCITT algorithm using a lookup table
            # XOR operations combine the current CRC state with the lookup table value
            new_crc = ((new_crc << 8) ^ CRC_TABLE[(new_crc >> 8) ^ byte]) & 0xFFFF
            # & 0xFFFF keeps the result as a 16-bit value (masks to 16 bits)
        
        return new_crc
    
    def status(self) -> bytes:
        """
        Send STATUS command (command 1) to check ePort device state
        
        This is like asking "what's your current status?" The ePort responds with a
        status code that tells us what's happening:
        - '6' = disabled, waiting for authorization
        - '3' = authorization declined
        - '9' = authorized and ready for dispensing
        
        Returns:
            Status response bytes from the ePort device
        """
        # Command 1 is just the ASCII character '1' (0x31) followed by carriage return
        command = bytearray([0x31, CR])  # '1' + CR (carriage return)
        self.ser.write(command)
        
        # Wait a bit for the device to process and respond (serial communication takes time)
        time.sleep(EPORT_COMMAND_DELAY)
        
        # Read the response line and remove whitespace (strip newlines, etc.)
        return self.ser.readline().strip()
    
    def reset(self):
        """
        Send RESET command (command 3) to reset the ePort device
        
        This clears the ePort's internal state and prepares it for a new transaction.
        Typically called before requesting authorization to ensure the device is in
        a known good state.
        """
        # Command 3 is the ASCII character '3' (0x33) followed by carriage return
        command = bytearray([0x33, CR])  # '3' + CR
        self.ser.write(command)
        time.sleep(EPORT_COMMAND_DELAY)  # Wait for reset to complete
    
    def request_authorization(self, amount_cents: int):
        """
        Send AUTH_REQ command (command 21) to authorize a credit card transaction
        
        This tells the ePort "please authorize $X.XX on the customer's card". The customer
        then swipes/inserts their card, and the ePort communicates with the payment processor
        to get approval or decline. We check the status afterward to see if it was approved.
        
        Command format: 21RS<amount>CRC16HICRC16LOCR
        Example: For $20.00 (2000 cents), the command would be: "21" + RS + "2000" + CRC bytes + CR
        
        Args:
            amount_cents: Authorization amount in cents (e.g., 2000 = $20.00)
                          This is a pre-authorization - the actual charge will be less
        """
        # Build the command payload: "21" + Record Separator + amount as string
        # 0x32 = ASCII '2', 0x31 = ASCII '1', so [0x32, 0x31] = "21"
        payload = bytearray([0x32, 0x31, RS])  # "21" + RS (Record Separator)
        payload.extend(str(amount_cents).encode('ascii'))  # Append amount as ASCII: "2000"
        
        # Calculate the CRC16 checksum for the payload (device requires this for validation)
        crc = self.calculate_crc16(payload)
        
        # Build the complete command: payload + CRC high byte + CRC low byte + carriage return
        command = bytearray(payload)
        command.append((crc >> 8) & 0xFF)  # CRC high byte (bits 15-8)
        command.append(crc & 0xFF)         # CRC low byte (bits 7-0)
        command.append(CR)                 # Carriage return marks end of command
        
        # Send the command to the ePort device via serial port
        self.ser.write(command)
        time.sleep(EPORT_COMMAND_DELAY)  # Wait for device to process the authorization request
    
    def send_transaction_result(self, quantity: int, price_cents: int, 
                                item_id: str, description: str) -> bool:
        """
        Send TRANSACTION_RESULT command (command 22) to complete the sale
        
        After the customer finishes dispensing product and presses "done", we send this
        command to tell the payment processor "charge $X.XX for this transaction". This
        completes the sale and the customer's card is charged the actual amount (which
        is usually less than the pre-authorization amount).
        
        Command format: 22RSLINE-ITEMSRSITEM-QUANTITYRSITEM-PRICERSITEM-IDRSITEM-DESCRIPTIONGSCrcCR
        - RS = Record Separator (0x1E)
        - GS = Group Separator (0x1D)
        - All fields are separated by RS, and GS marks the end of item data
        
        Args:
            quantity: Number of items sold (typically 1 for this vending machine)
            price_cents: Final transaction price in cents (e.g., 35 = $0.35)
            item_id: Item identifier string (0-5 digits, used for reporting)
            description: Item description (max 30 bytes, e.g., "oz hand wash")
            
        Returns:
            True if command sent successfully (doesn't guarantee device accepted it)
        """
        # For this vending machine, we always have exactly 1 line item
        line_items = "1"
        
        # Build the command payload (everything except CRC and CR)
        payload = bytearray()
        payload.extend(b"22")  # Command 22 (TRANSACTION_RESULT)
        payload.append(RS)     # Record Separator
        
        # Add each field separated by RS (Record Separator)
        payload.extend(line_items.encode('ascii'))      # Number of line items: "1"
        payload.append(RS)
        payload.extend(str(quantity).encode('ascii'))   # Quantity: "1"
        payload.append(RS)
        payload.extend(str(price_cents).encode('ascii')) # Price in cents: "35"
        payload.append(RS)
        payload.extend(item_id.encode('ascii'))         # Item ID: "1"
        payload.append(RS)
        payload.extend(description[:30].encode('ascii')) # Description (max 30 bytes): "oz hand wash"
        payload.append(GS)     # Group Separator marks end of item data
        
        # Calculate CRC16 checksum for the payload
        crc = self.calculate_crc16(payload)
        
        # Build the complete command: payload + CRC bytes + carriage return
        command = bytearray(payload)
        command.append((crc >> 8) & 0xFF)  # CRC high byte (upper 8 bits)
        command.append(crc & 0xFF)         # CRC low byte (lower 8 bits)
        command.append(CR)                 # Carriage return marks end of command
        
        # Send the command to the ePort device
        self.ser.write(command)
        time.sleep(EPORT_COMMAND_DELAY)  # Wait for device to process
        
        return True
    
    def get_transaction_id(self) -> Optional[str]:
        """
        Request transaction ID (command 13) from the ePort device
        
        The transaction ID is a unique identifier for this sale. It's useful for
        record-keeping and troubleshooting, but not critical for the machine to function.
        
        The ePort responds to command 13 via a status response with format: 17RSTransaction_IDCR
        So we send command 13, then read the status to get the ID.
        
        Returns:
            Transaction ID as string (e.g., "12345678"), or None if not available/parsed
        """
        # Command 13 is "13" in ASCII: 0x31='1', 0x33='3'
        command = bytearray([0x31, 0x33, CR])  # "13" + CR
        self.ser.write(command)
        time.sleep(EPORT_COMMAND_DELAY)
        
        # Get the response by sending a STATUS command (the ePort returns the ID in status response)
        response = self.status()
        
        # Response format: "17" + RS + Transaction_ID + CR
        # "17" indicates this is a transaction ID response
        if response.startswith(b'17'):
            # Split on Record Separator to get the ID part
            parts = response.split(bytes([RS]))
            if len(parts) >= 2:
                # parts[0] = "17", parts[1] = Transaction_ID
                # Decode from bytes to string and strip whitespace
                return parts[1].decode('ascii').strip()
        
        # If response doesn't match expected format, return None
        return None
