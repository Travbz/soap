# Serial ePort Protocol Reference

**Revision:** 18  
**Manufacturer:** USA Technologies Inc.  
**Device:** ePort Telemeter

---

## Overview

This document describes the serial protocol for interfacing with the ePort credit card reader device. The ePort acts as a slave device that responds to commands from a master Kiosk/Terminal.

---

## Hardware Configuration

- **Baud Rate:** 9600
- **Data Bits:** 8
- **Parity:** None
- **Stop Bits:** 1
- **Flow Control:** None

**Interface:** 9600-8-N-1 without flow control

---

## Communication Protocol

### Protocol Characteristics

1. **Master-Slave Architecture**
   - Kiosk (Master) initiates all communication
   - ePort (Slave) responds to each command
   - Some responses require a STATUS command to retrieve

2. **Character Set**
   - Printable ASCII characters
   - Special control characters (see below)

3. **Timing**
   - ePort ACKs commands within 10ms
   - Recommended: Poll with STATUS command every few seconds during idle

### Control Characters

| Character | Hex | Purpose |
|-----------|-----|---------|
| ACK | 0x06 | Acknowledge |
| NAK | 0x15 | Not-acknowledge |
| RS (Record Separator) | 0x1E | Separates data elements |
| GS (Group Separator) | 0x1D | Separates blocks of related data |
| LS (Language Separator) | 0x7C | Separates different language data |
| CR (Carriage Return) | 0x0D | Terminates commands/responses |

### CRC16 Checksum

- **Required:** Append to all commands with additional data
- **Algorithm:** CRC16-CCITT (see implementation below)
- **Format:** 2-byte value appended before CR

---

## Transaction Methods

### Method 1: Preauthorization/Sale

**Use Case:** When product price varies greatly

**Flow:**
1. Kiosk starts with ePort **disabled** (prevents card swipe)
2. Customer selects product
3. Kiosk determines preauth amount
4. Kiosk **enables** ePort
5. Customer swipes/taps card
6. If approved: Deliver product, complete sale
7. If declined: Terminate transaction
8. Kiosk **disables** ePort

**Important:** Keep preauth and sale amounts similar to avoid:
- Customer disputes (preauth too high)
- Device lockout (sale > 3× preauth)

### Method 2: Charge

**Use Case:** When product price is fixed or varies little

**Flow:**
1. Kiosk keeps ePort **enabled**
2. Customer initiates by swiping card
3. ePort checks card with fixed preauth
4. If approved: Customer selects product, delivery, complete sale
5. If declined: Terminate transaction
6. Kiosk **re-enables** ePort for next customer

---

## Command Reference

### Command 1: STATUS

**Purpose:** Check ePort device state

**Format:**
```
'1' + CR
```

**Response Codes:**
- `6` - Disabled, waiting for authorization
- `3` - Authorization declined
- `9` - Authorized and ready for dispensing
- `17` - Transaction ID response (after command 13)

**Example:**
```
Send: 0x31 0x0D (ASCII: "1" + CR)
Receive: 0x36 (ASCII: "6" - disabled state)
```

---

### Command 3: RESET

**Purpose:** Reset ePort device to clear state

**Format:**
```
'3' + CR
```

**Usage:** Call before requesting authorization to ensure clean state

**Example:**
```
Send: 0x33 0x0D (ASCII: "3" + CR)
```

---

### Command 13: REQUEST TRANSACTION ID

**Purpose:** Retrieve unique transaction identifier

**Format:**
```
'1' '3' + CR
```

**Response:** Follow with STATUS command (Command 1)

**Response Format:**
```
"17" + RS + Transaction_ID + CR
```

**Example:**
```
Send: 0x31 0x33 0x0D (ASCII: "13" + CR)
Then send STATUS: 0x31 0x0D
Receive: "17" + RS + "12345678" + CR
```

---

### Command 21: AUTH_REQ (Authorization Request)

**Purpose:** Request credit card authorization

**Format:**
```
'2' '1' + RS + <amount_cents> + CRC_HI + CRC_LO + CR
```

**Parameters:**
- `amount_cents` - Authorization amount in cents (e.g., "2000" = $20.00)

**Example: $3.50 Authorization**
```
Payload: "21" + RS + "350"
CRC16: E558
Command: 32 31 1E 33 35 30 E5 58 0D
```

**After Sending:** Poll with STATUS to check authorization result

---

### Command 22: TRANSACTION_RESULT (Complete Sale)

**Purpose:** Send final transaction amount and item details

**Format:**
```
'2' '2' + RS + LINE_ITEMS + RS + QUANTITY + RS + PRICE + RS + ITEM_ID + RS + DESCRIPTION + GS + CRC_HI + CRC_LO + CR
```

**Parameters:**
- `LINE_ITEMS` - Number of line items (typically "1")
- `QUANTITY` - Quantity sold (typically "1")
- `PRICE` - Final price in cents (e.g., "350" = $3.50)
- `ITEM_ID` - Item identifier (0-5 digits, for reporting)
- `DESCRIPTION` - Item description (max 30 bytes)

**Example: $0.35 for "oz hand wash"**
```
Payload: "22" + RS + "1" + RS + "1" + RS + "35" + RS + "1" + RS + "oz hand wash" + GS
CRC: (calculated from payload)
Command: [payload bytes] + [CRC bytes] + CR
```

**Result:** Card is charged the final amount (usually ≤ preauth)

---

## Status Codes

### Common Status Responses

| Code | Meaning | Action |
|------|---------|--------|
| `6` | Disabled | Ready to request authorization |
| `9` | Authorized | Customer can dispense product |
| `3` | Declined | Card declined, terminate transaction |
| `17` | Transaction ID | Response contains transaction ID |

---

## CRC16 Calculation

### Algorithm

The CRC16-CCITT algorithm is used for error detection.

**C Implementation:**
```c
unsigned short calculate_crc16(char *data_ptr, unsigned short data_length)
{
    unsigned short index;
    unsigned short new_crc = 0xFFFF;
    
    // Loop through the entire buffer array of data
    for (index = 0; index < data_length; index++)
    {
        new_crc = (new_crc << 8) ^ crc_table[(new_crc >> 8) ^ (*data_ptr++)];
    }
    
    return(new_crc);
}
```

**Python Implementation:**
```python
def calculate_crc16(data: bytearray) -> int:
    """Calculate CRC16 checksum using CRC16-CCITT algorithm"""
    new_crc = 0xFFFF
    
    for byte in data:
        new_crc = ((new_crc << 8) ^ CRC_TABLE[(new_crc >> 8) ^ byte]) & 0xFFFF
    
    return new_crc
```

**CRC Lookup Table:**
```python
CRC_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
]
```

**Usage:**
1. Calculate CRC from first byte of message (including control characters)
2. Append CRC as 2 bytes: `CRC_HI`, `CRC_LO`
3. CRC_HI = `(crc >> 8) & 0xFF` (upper 8 bits)
4. CRC_LO = `crc & 0xFF` (lower 8 bits)

---

## Error Codes

### Bank Decline Codes (Test Values)

The ePort supports test transactions using specific cent values to simulate errors:

| Amount | Error Text | Error Number | Notes |
|--------|------------|--------------|-------|
| $x.01 | AUTH DECLINED | 200 | Generic decline |
| $x.02 | CALL VOICE OPER | 201 | Requires voice authorization |
| $x.03 | HOLD - CALL | 202 | Hold card, call issuer |
| $x.05 | INVALID CARD NO | 204 | Invalid card number |
| $x.06 | INVALID EXP DATE | 205 | Expired card |
| $x.14 | DECLINE | 213 | Generic decline |
| $x.16 | LOST/STOLEN CARD | 215 | Card reported lost/stolen |
| $x.17 | INVALID PIN | 216 | Incorrect PIN |
| $x.18 | OVER CREDIT FLR | 217 | Exceeds credit limit |
| $x.59 | DECLINED PER CARDHOLDER | - | Cardholder requested decline |
| $19.58 | Returns 'D' in Auth Code | - | VISA only |
| $98.26-$98.91 | PSERV=N; Downgrade Reason = NP | - | VISA only |
| > $999,999.99 | INVALID AMOUNT | 319 | Maximum transaction limit |

**Note:** Use these test amounts during development to simulate various error conditions.

---

## Best Practices

### 1. Polling Strategy
- Poll with STATUS command every 2-5 seconds during idle
- Ensures ePort remains active and responsive

### 2. Error Handling
- Always check ACK/NAK responses
- Implement timeout handling (10ms for ACK)
- Retry failed commands with exponential backoff

### 3. Transaction Flow
- Always RESET before requesting authorization
- Keep preauth and sale amounts similar (avoid 3× difference)
- Disable ePort between transactions to prevent accidental swipes

### 4. CRC Validation
- Always include CRC for commands with data
- Validate CRC on responses containing data
- Use lookup table for performance

### 5. State Management
- Track ePort state (disabled/authorized/declined)
- Only allow card swipes when in correct state
- Handle unexpected state transitions gracefully

---

## Common Issues & Solutions

### Issue: Device Lockout
**Cause:** Sale amount > 3× preauthorization amount  
**Solution:** Keep preauth and expected sale amounts similar  
**Recovery:** Contact USAT Technical Support to re-enable device

### Issue: Customer Disputes
**Cause:** Preauthorization hold appears as charge  
**Solution:** Set reasonable preauth amounts, educate customers about holds

### Issue: ACK Timeout
**Cause:** ePort not responding within 10ms  
**Solution:** Check serial connection, verify baud rate, send RESET command

### Issue: CRC Mismatch
**Cause:** Incorrect CRC calculation or data corruption  
**Solution:** Verify CRC algorithm, check for correct data length, inspect serial cable

---

## Quick Reference

### Essential Commands

| Command | Code | Format | Purpose |
|---------|------|--------|---------|
| STATUS | 1 | `'1' + CR` | Check device state |
| RESET | 3 | `'3' + CR` | Reset device |
| AUTH_REQ | 21 | `'21' + RS + amount + CRC + CR` | Request authorization |
| TRANSACTION_RESULT | 22 | `'22' + RS + items + ... + GS + CRC + CR` | Complete sale |
| GET_TRANS_ID | 13 | `'13' + CR` | Get transaction ID |

### Common Status Codes

| Code | State | Next Action |
|------|-------|-------------|
| 6 | Disabled | Request authorization (command 21) |
| 9 | Authorized | Dispense product, send transaction result |
| 3 | Declined | Terminate transaction, show error |

### Serial Settings

```
9600 baud, 8 data bits, No parity, 1 stop bit
No flow control
```

---

## Additional Functions

The ePort supports additional functions beyond basic credit card processing:

1. **Time Synchronization** - Acquire current time from ePort
2. **Configuration Upload** - Send kiosk config to USAT server for reporting
3. **File Transfer** - Send files to server (up to 900 bytes ASCII)
4. **Remote File Delivery** - Receive files from USAT (requires support assistance)
5. **Device Reboot** - Remote reboot capability

**Note:** Contact USAT Technical Support for detailed documentation on advanced functions.

---

## Support

**USA Technologies Inc.**  
**Location:** Tennessee, USA

For technical support or device re-enablement, contact USAT Technical Support.

---

**Document Status:** Reference Implementation  
**Based On:** Serial ePort Protocol - Revision 18  
**For:** Raspberry Pi Vending Machine Controller Project
