"""
Configuration constants for ePort protocol and machine settings
"""

# CRC16 lookup table from Serial ePort Protocol Appendix B (page 21-22)
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

# Protocol constants from Serial ePort Protocol
RS = 0x1E  # Record Separator
GS = 0x1D  # Group Separator
CR = 0x0D  # Carriage Return
ACK = 0x06  # Acknowledge
NAK = 0x15  # Not-acknowledge

# Serial port settings
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUDRATE = 9600
SERIAL_TIMEOUT = 1

# Machine hardware configuration
MOTOR_PIN = 17
FLOWMETER_PIN = 24
PRODUCT_BUTTON_PIN = 4
DONE_BUTTON_PIN = 27

# Product configuration
PRODUCT_PRICE = 0.15  # Price per ounce in dollars
PRODUCT_UNIT = 'oz hand wash'
FLOWMETER_PULSES_PER_OUNCE = 5.4  # Calibration: pulses per ounce

# Retry and error handling configuration
MAX_RETRIES = 3  # Default number of retries for operations
RETRY_DELAY = 5  # Seconds to wait between retries
STATUS_POLL_INTERVAL = 1  # Seconds between status checks
SERIAL_OPEN_RETRIES = 5  # Number of attempts to open serial connection
MAX_CONSECUTIVE_ERRORS = 10  # Maximum consecutive errors before shutdown
MAX_MOTOR_ERRORS = 5  # Maximum motor control errors before exiting dispensing mode
MAX_TRANSACTION_PRICE = 1000.0  # Maximum transaction price in dollars

# Authorization configuration
AUTH_AMOUNT_CENTS = 2000  # Default authorization amount in cents ($20.00)

# Timing configuration (all values in seconds unless otherwise specified)
# ePort communication delays
EPORT_COMMAND_DELAY = 0.5  # Wait time after sending commands to ePort (status, reset, auth, transaction)
EPORT_INIT_DELAY = 0.5  # Wait time for ePort device to initialize after serial connection

# Machine control loop delays
MOTOR_CONTROL_LOOP_DELAY = 0.1  # Sleep time in dispensing loop to prevent CPU spinning
MOTOR_OFF_DEBOUNCE_DELAY = 0.7  # Delay before turning motor off when button released (prevents rapid cycling)
MOTOR_ERROR_RETRY_DELAY = 0.5  # Wait time before retrying after motor control error

# Button debouncing
DONE_BUTTON_SOFTWARE_DEBOUNCE_DELAY = 0.01  # Software debounce check delay (10ms)
DONE_BUTTON_HARDWARE_DEBOUNCE_MS = 500  # Hardware debounce time in milliseconds (GPIO bouncetime)

# Status check and error handling delays
AUTHORIZATION_STATUS_CHECK_DELAY = 1.0  # Wait time after authorization request before checking status
POST_RESET_DELAY = 0.5  # Wait time after reset before requesting authorization (reduced for faster display)
DECLINED_CARD_RETRY_DELAY = 1.0  # Wait time before checking status again after declined card

# Multi-product configuration
PRODUCTS_CONFIG_PATH = 'ePort/config/products.json'  # Path to products configuration file (relative to project root)
MAX_ITEMS_PER_TRANSACTION = 10  # Maximum number of different products per transaction (prevent abuse)
PRODUCT_SWITCH_DELAY = 0.5  # Delay when switching between products in seconds (prevents rapid switching)

# Dispensing session timeouts (prevent abandoned sessions blocking machine)
DISPENSING_INACTIVITY_TIMEOUT = 60  # Seconds of no button activity before auto-completing transaction
DISPENSING_MAX_SESSION_TIME = 300   # Maximum session duration in seconds (5 minutes total) prevents abuse and sets expectations might wanna increase?? @adam
INACTIVITY_WARNING_TIME = 45        # Seconds before timeout to display warning to customer
WAITING_SCREEN_TIMEOUT = 0.5       # Seconds of no button press to show "Press Done" waiting screen

# Display server configuration
DISPLAY_ENABLED = True              # Required for production - only set to False for development/testing
DISPLAY_HOST = 'localhost'          # Display server host
DISPLAY_PORT = 5000                 # Display server port
RECEIPT_DISPLAY_TIMEOUT = 10        # Seconds to show receipt before returning to idle
ERROR_DISPLAY_TIMEOUT = 10          # Seconds to show error before reset attempt

# Logging configuration
TX_LOG_FILE = 'last_tx_log.log'     # Transaction log file (overwritten each run to save disk on Pi)
