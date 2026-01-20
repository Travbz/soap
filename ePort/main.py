#!/usr/bin/env python3
"""
Vending Machine Controller - Main Entry Point
Continuously monitors for customers and processes soap dispensing transactions
"""

import sys
import time
import serial
import logging
import traceback
from typing import Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    # For testing without hardware
    print("Warning: RPi.GPIO not available - using mock GPIO")
    GPIO = None

from .src.payment import EPortProtocol
from .src.machine import MachineController
from .config import (
    SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT,
    MOTOR_PIN, FLOWMETER_PIN, PRODUCT_BUTTON_PIN, DONE_BUTTON_PIN,
    PRODUCT_PRICE, PRODUCT_UNIT, FLOWMETER_PULSES_PER_OUNCE,
    MAX_RETRIES, RETRY_DELAY, STATUS_POLL_INTERVAL, SERIAL_OPEN_RETRIES,
    MAX_CONSECUTIVE_ERRORS, MAX_MOTOR_ERRORS, MAX_TRANSACTION_PRICE,
    AUTH_AMOUNT_CENTS,
    CR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VendingMachineError(Exception):
    """Base exception for vending machine errors"""
    pass


class SerialConnectionError(VendingMachineError):
    """Error connecting to serial port"""
    pass


class PaymentProtocolError(VendingMachineError):
    """Error in payment protocol communication"""
    pass


class MachineHardwareError(VendingMachineError):
    """Error in machine hardware operations"""
    pass


def setup_serial_connection() -> serial.Serial:
    """
    Initialize serial connection to ePort with retry logic
    
    Uses SERIAL_OPEN_RETRIES from config for number of retry attempts.
    
    Returns:
        Serial connection object
        
    Raises:
        SerialConnectionError: If connection cannot be established
    """
    logger.info(f"Attempting to connect to ePort on {SERIAL_PORT}")
    
    for attempt in range(1, SERIAL_OPEN_RETRIES + 1):
        try:
            ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=SERIAL_BAUDRATE,
                timeout=SERIAL_TIMEOUT,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Test connection with a status check
            time.sleep(0.5)  # Give device time to initialize
            logger.info(f"Serial connection established to {SERIAL_PORT}")
            return ser
            
        except serial.SerialException as e:
            error_msg = f"Serial connection attempt {attempt}/{SERIAL_OPEN_RETRIES} failed: {e}"
            logger.warning(error_msg)
            
            if attempt < SERIAL_OPEN_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise SerialConnectionError(
                    f"Failed to connect to {SERIAL_PORT} after {SERIAL_OPEN_RETRIES} attempts: {e}"
                )
        
        except Exception as e:
            raise SerialConnectionError(f"Unexpected error opening serial port: {e}")
    
    raise SerialConnectionError("Serial connection failed - maximum retries exceeded")


def setup_gpio():
    """
    Initialize GPIO with error handling
    
    Returns:
        GPIO module object
        
    Raises:
        MachineHardwareError: If GPIO cannot be initialized
    """
    if GPIO is None:
        raise MachineHardwareError("RPi.GPIO not available - cannot initialize hardware")
    
    try:
        GPIO.setmode(GPIO.BCM)
        logger.info("GPIO initialized successfully")
        return GPIO
    except Exception as e:
        raise MachineHardwareError(f"Failed to initialize GPIO: {e}")


def safe_status_check(payment: EPortProtocol, retries: int = None) -> Optional[bytes]:
    """
    Safely check ePort status with retry logic
    
    Uses MAX_RETRIES from config if retries not specified.
    
    Args:
        payment: EPortProtocol instance
        retries: Number of retry attempts (defaults to MAX_RETRIES from config)
        
    Returns:
        Status response bytes, or None if all retries fail
    """
    if retries is None:
        retries = MAX_RETRIES
    
    for attempt in range(1, retries + 1):
        try:
            status = payment.status()
            return status
        except Exception as e:
            logger.warning(f"Status check attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(1)
            else:
                logger.error(f"Status check failed after {retries} attempts: {e}")
                return None
    return None


def safe_authorization_request(payment: EPortProtocol, amount_cents: int, retries: int = None) -> bool:
    """
    Safely request authorization with retry logic
    
    Uses MAX_RETRIES from config if retries not specified.
    
    Args:
        payment: EPortProtocol instance
        amount_cents: Authorization amount in cents
        retries: Number of retry attempts (defaults to MAX_RETRIES from config)
        
    Returns:
        True if successful, False otherwise
    """
    if retries is None:
        retries = MAX_RETRIES
    
    for attempt in range(1, retries + 1):
        try:
            payment.request_authorization(amount_cents)
            logger.info(f"Authorization requested for ${amount_cents / 100:.2f}")
            return True
        except Exception as e:
            logger.warning(f"Authorization request attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(1)
            else:
                logger.error(f"Authorization request failed after {retries} attempts: {e}")
                return False
    return False


def safe_reset(payment: EPortProtocol) -> bool:
    """
    Safely reset ePort device
    
    Args:
        payment: EPortProtocol instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        payment.reset()
        logger.info("ePort reset successful")
        return True
    except Exception as e:
        logger.error(f"ePort reset failed: {e}")
        return False


def safe_transaction_result(payment: EPortProtocol, quantity: int, price_cents: int,
                            item_id: str, description: str, retries: int = None) -> bool:
    """
    Safely send transaction result with retry logic
    
    Uses MAX_RETRIES from config if retries not specified.
    
    Args:
        payment: EPortProtocol instance
        quantity: Number of items sold
        price_cents: Price in cents
        item_id: Item identifier
        description: Item description
        retries: Number of retry attempts (defaults to MAX_RETRIES from config)
        
    Returns:
        True if successful, False otherwise
    """
    if retries is None:
        retries = MAX_RETRIES
    
    for attempt in range(1, retries + 1):
        try:
            success = payment.send_transaction_result(
                quantity=quantity,
                price_cents=price_cents,
                item_id=item_id,
                description=description
            )
            if success:
                print(f"Transaction result sent successfully: ${price_cents / 100:.2f}")
                logger.debug(f"Transaction result sent successfully: ${price_cents / 100:.2f}")
                return True
            else:
                logger.warning(f"Transaction result returned False on attempt {attempt}")
        except Exception as e:
            logger.warning(f"Transaction result attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(1)
    
    logger.error(f"Transaction result failed after {retries} attempts")
    return False


def cleanup_resources(ser: Optional[serial.Serial], gpio):
    """
    Clean up hardware resources
    
    Args:
        ser: Serial connection (if exists)
        gpio: GPIO module
    """
    try:
        if ser and ser.is_open:
            ser.close()
            logger.info("Serial connection closed")
    except Exception as e:
        logger.error(f"Error closing serial connection: {e}")
    
    try:
        if gpio:
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"Error cleaning up GPIO: {e}")


def main():
    """Main application loop with comprehensive error handling"""
    
    ser = None
    gpio = None
    payment = None
    machine = None
    
    try:
        # Initialize GPIO
        logger.info("Initializing GPIO...")
        gpio = setup_gpio()
        
        # Initialize serial connection
        logger.info("Initializing serial connection...")
        ser = setup_serial_connection()
        
        # Initialize payment protocol handler
        logger.info("Initializing payment protocol handler...")
        payment = EPortProtocol(ser)
        
        # Initialize machine controller
        logger.info("Initializing machine controller...")
        try:
            machine = MachineController(
                gpio=gpio,
                motor_pin=MOTOR_PIN,
                flowmeter_pin=FLOWMETER_PIN,
                product_button_pin=PRODUCT_BUTTON_PIN,
                done_button_pin=DONE_BUTTON_PIN,
                price_per_ounce=PRODUCT_PRICE,
                pulses_per_ounce=FLOWMETER_PULSES_PER_OUNCE,
                product_unit=PRODUCT_UNIT
            )
            logger.info("Machine controller initialized successfully")
        except Exception as e:
            raise MachineHardwareError(f"Failed to initialize machine controller: {e}")
        
        logger.info("=" * 60)
        logger.info("Vending machine controller started")
        logger.info(f"Product: {PRODUCT_UNIT}")
        logger.info(f"Price: ${PRODUCT_PRICE}/ounce")
        logger.info("=" * 60)
        
        # Main loop - continuously monitor for customers
        consecutive_errors = 0
        
        while True:
            try:
                # Poll ePort status
                status = safe_status_check(payment)
                
                if status is None:
                    consecutive_errors += 1
                    logger.error(f"Status check failed (consecutive errors: {consecutive_errors})")
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.critical(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                        break
                    time.sleep(RETRY_DELAY)
                    continue
                
                consecutive_errors = 0  # Reset on success
                logger.debug(f"Status: {status}")
                
                # Check if ePort is disabled (code 6)
                if status == b'6':
                    logger.info("ePort disabled - resetting and requesting authorization")
                    
                    if not safe_reset(payment):
                        logger.error("Reset failed - skipping authorization request")
                        time.sleep(RETRY_DELAY)
                        continue
                    
                    time.sleep(1)
                    
                    # Request authorization
                    if not safe_authorization_request(payment, AUTH_AMOUNT_CENTS):
                        logger.error("Authorization request failed")
                        time.sleep(RETRY_DELAY)
                        continue
                    
                    # Check authorization status
                    time.sleep(1)
                    auth_status = safe_status_check(payment)
                    if auth_status:
                        logger.info(f"Auth status: {auth_status}")
                    else:
                        logger.warning("Failed to get auth status")
                        
                # Check if authorization declined (code 3)
                elif status.startswith(b'3'):
                    logger.warning("Authorization declined by bank")
                    # Handle declined transaction - wait before retrying
                    time.sleep(RETRY_DELAY)
                    
                # Check if waiting for transaction result (code 9)
                # This means card was approved and customer can dispense
                elif status == b'9':
                    logger.info("Authorization approved - enabling dispensing")
                    try:
                        handle_dispensing(machine, payment)
                    except KeyboardInterrupt:
                        logger.info("Dispensing interrupted by user")
                        raise
                    except Exception as e:
                        logger.error(f"Error during dispensing: {e}")
                        logger.error(traceback.format_exc())
                        # Reset machine state on error
                        try:
                            machine.reset()
                        except Exception as reset_error:
                            logger.error(f"Error resetting machine: {reset_error}")
                        time.sleep(RETRY_DELAY)
                
                # Brief delay before next status check
                time.sleep(STATUS_POLL_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested by user")
                break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in main loop (consecutive errors: {consecutive_errors}): {e}")
                logger.error(traceback.format_exc())
                
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                    break
                
                time.sleep(RETRY_DELAY)
    
    except SerialConnectionError as e:
        logger.critical(f"Serial connection error: {e}")
        sys.exit(1)
        
    except MachineHardwareError as e:
        logger.critical(f"Hardware initialization error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.critical(f"Fatal error during initialization: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
        
    finally:
        logger.info("Shutting down vending machine controller...")
        cleanup_resources(ser, gpio)
        logger.info("Vending machine controller stopped")


def handle_dispensing(machine: MachineController, payment: EPortProtocol):
    """
    Handle the dispensing phase after authorization is approved
    
    This function manages the entire dispensing session after a card is authorized.
    The customer can press and hold the product button to dispense, and press the
    done button when finished. This function runs until the transaction is complete.
    
    Flow:
    1. Set up callbacks for flowmeter pulses and done button
    2. Enter a loop that monitors the product button and controls the motor
    3. When done button is pressed, send transaction result to payment processor
    4. Reset machine state for next customer
    
    Args:
        machine: MachineController instance (handles GPIO, motors, sensors)
        payment: EPortProtocol instance (communicates with ePort card reader)
    
    Raises:
        PaymentProtocolError: If transaction completion fails
        MachineHardwareError: If hardware operations fail
    """
    
    # Flag to signal that transaction is complete or cancelled
    # This allows the callback to exit the dispensing loop
    transaction_complete = False
    
    def on_flowmeter_pulse(ounces: float, price: float):
        """
        Callback function called automatically each time the flowmeter sends a pulse
        
        This runs in the background as product flows. We just log it for debugging,
        but the MachineController already tracks the total ounces and price internally.
        
        Args:
            ounces: Total ounces dispensed so far
            price: Total price calculated so far (in dollars)
        """
        try:
            # Log each pulse in real-time (use debug level to keep output clean)
            # Change to logger.info() if you want to see flowmeter output during operation
            logger.debug(f"Flowmeter pulse: {ounces:.3f} oz - ${price:.2f}")
        except Exception as e:
            logger.error(f"Error in flowmeter callback: {e}")
    
    def on_done_button():
        """
        Callback function called automatically when customer presses the "done" button
        
        This is where we complete the transaction. The customer has finished dispensing
        product and pressed "done", so we:
        1. Get the final ounces and price
        2. Validate the transaction (make sure product was dispensed, price is reasonable)
        3. Send the transaction result to the payment processor to charge the card
        4. Reset the machine for the next customer
        
        This function runs inside a GPIO interrupt handler, so it needs to handle
        errors gracefully without crashing the main loop.
        """
        # Declare nonlocal at the top of the function (required by Python)
        nonlocal transaction_complete
        
        try:
            # Get the final dispense information (total ounces and price)
            ounces, price = machine.get_dispense_info()
            
            # Safety check: If no product was dispensed (price = 0), don't charge anything
            if price <= 0:
                logger.warning("Done button pressed but no product dispensed - cancelling transaction")
                machine.reset()
                # Signal that transaction is cancelled so the dispensing loop exits
                transaction_complete = True
                return
            
            # Display transaction details to customer (clean output, no timestamps)
            print(f"\nOunces: {ounces:.3f}")
            print(f"Price: ${price:.2f}")
            
            # Safety check: Prevent charging more than MAX_TRANSACTION_PRICE (prevents errors/abuse)
            if price > MAX_TRANSACTION_PRICE:
                logger.error(f"Price too high: ${price:.2f} - refusing transaction")
                machine.reset()
                # Signal that transaction is cancelled so the dispensing loop exits
                transaction_complete = True
                return
            
            # Convert price from dollars to cents for the payment processor
            # Example: $0.35 → 35 cents
            price_cents = int(round(price * 100))
            
            # Send the transaction result to the ePort/payment processor
            # This tells them "charge $X.XX for this transaction"
            # If this fails, the transaction didn't complete properly
            if not safe_transaction_result(
                payment=payment,
                quantity=1,  # We always sell 1 "item" (the dispensed amount)
                price_cents=price_cents,  # Final price in cents
                item_id="1",  # Item identifier (used for reporting)
                description=PRODUCT_UNIT[:30]  # Description, max 30 bytes
            ):
                raise PaymentProtocolError("Failed to send transaction result")
            
            # Try to get the transaction ID (useful for records, but not critical)
            # If this fails, we don't want to fail the whole transaction
            try:
                transaction_id = payment.get_transaction_id()
                if transaction_id:
                    logger.info(f"Transaction ID: {transaction_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve transaction ID: {e}")
            
            # Reset the machine state (clear counters, remove callbacks)
            # This prepares the machine for the next customer
            machine.reset()
            print("Machine reset - ready for next customer\n")
            logger.debug("Machine reset - ready for next customer")
            
            # Signal that transaction is complete so the dispensing loop exits
            transaction_complete = True
            
        except PaymentProtocolError:
            # Re-raise payment protocol errors
            raise
        except Exception as e:
            logger.error(f"Error in done button callback: {e}")
            logger.error(traceback.format_exc())
            try:
                machine.reset()
            except Exception as reset_error:
                logger.error(f"Error resetting machine after callback error: {reset_error}")
            raise MachineHardwareError(f"Error completing transaction: {e}")
    
    # Start dispensing mode - set up callbacks and reset counters
    try:
        machine.start_dispensing(
            flowmeter_callback=on_flowmeter_pulse,  # Called each time flowmeter pulses
            done_callback=on_done_button            # Called when customer presses "done"
        )
        logger.info("Dispensing enabled - press button to dispense")
    except Exception as e:
        raise MachineHardwareError(f"Failed to start dispensing mode: {e}")
    
    # Main control loop - continuously monitor product button and control motor
    # This loop runs until the customer presses "done" (which triggers the callback
    # and sets transaction_complete = True) or an error occurs
    motor_error_count = 0
    
    try:
        while not transaction_complete:
            try:
                # Control motor based on product button state
                # When customer presses and holds button: motor runs (dispenses product)
                # When customer releases button: motor stops
                if machine.is_product_button_pressed():
                    machine.control_motor(True)  # Turn motor ON (dispense product)
                else:
                    # Button released - add a small delay before turning off
                    # This prevents rapid on/off cycling if the button bounces
                    time.sleep(0.7)  # Brief delay for debouncing (prevents rapid cycling)
                    machine.control_motor(False)  # Turn motor OFF (stop dispensing)
                
                motor_error_count = 0  # Reset error counter on successful iteration
                
                # Small sleep to prevent CPU from spinning at 100% usage
                # This loop runs very fast, so we add a tiny delay
                time.sleep(0.1)
                
            except Exception as e:
                motor_error_count += 1
                logger.warning(f"Error controlling motor (error {motor_error_count}/{MAX_MOTOR_ERRORS}): {e}")
                
                if motor_error_count >= MAX_MOTOR_ERRORS:
                    logger.error("Too many motor control errors - exiting dispensing mode")
                    raise MachineHardwareError("Motor control failed repeatedly")
                
                time.sleep(0.5)  # Wait before retrying
            
    except KeyboardInterrupt:
        logger.info("Dispensing interrupted")
        raise
    except MachineHardwareError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in dispensing loop: {e}")
        logger.error(traceback.format_exc())
        raise MachineHardwareError(f"Dispensing loop error: {e}")
    finally:
        # Always reset machine state when exiting dispensing mode
        try:
            machine.reset()
        except Exception as e:
            logger.error(f"Error resetting machine in finally block: {e}")


if __name__ == "__main__":
    main()
