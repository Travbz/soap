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
from .src.product_manager import ProductManager
from .src.transaction_tracker import TransactionTracker
from .config import (
    SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT,
    DONE_BUTTON_PIN,
    MAX_RETRIES, RETRY_DELAY, STATUS_POLL_INTERVAL, SERIAL_OPEN_RETRIES,
    MAX_CONSECUTIVE_ERRORS, MAX_MOTOR_ERRORS, MAX_TRANSACTION_PRICE,
    AUTH_AMOUNT_CENTS,
    CR,
    EPORT_INIT_DELAY,
    AUTHORIZATION_STATUS_CHECK_DELAY,
    POST_RESET_DELAY,
    DECLINED_CARD_RETRY_DELAY,
    MOTOR_CONTROL_LOOP_DELAY,
    MOTOR_OFF_DEBOUNCE_DELAY,
    MOTOR_ERROR_RETRY_DELAY,
    PRODUCTS_CONFIG_PATH,
    PRODUCT_SWITCH_DELAY,
    MAX_ITEMS_PER_TRANSACTION,
    DISPENSING_INACTIVITY_TIMEOUT,
    DISPENSING_MAX_SESSION_TIME,
    INACTIVITY_WARNING_TIME,
    WAITING_SCREEN_TIMEOUT,
    DISPLAY_ENABLED,
    DISPLAY_HOST,
    DISPLAY_PORT,
    RECEIPT_DISPLAY_TIMEOUT,
    ERROR_DISPLAY_TIMEOUT
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
            time.sleep(EPORT_INIT_DELAY)  # Give device time to initialize
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
                time.sleep(RETRY_DELAY)
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
                time.sleep(RETRY_DELAY)
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
                time.sleep(RETRY_DELAY)
    
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


def check_and_run_setup():
    """Check if setup is needed and run it automatically"""
    import os
    import subprocess
    
    # Check if dependencies are installed
    missing = []
    try:
        import flask, flask_socketio
    except ImportError:
        missing.append("flask")
    
    try:
        import serial
    except ImportError:
        missing.append("serial")
    
    try:
        import RPi.GPIO
    except ImportError:
        missing.append("GPIO")
    
    if not missing:
        return True  # All good
    
    # Dependencies missing - run setup automatically
    logger.info("=" * 60)
    logger.info("FIRST TIME SETUP DETECTED")
    logger.info("=" * 60)
    logger.info("Running automated setup...")
    
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'setup.sh')
    
    try:
        result = subprocess.run(['bash', script_path], check=True)
        logger.info("Setup completed successfully!")
        logger.info("Please reboot the system: sudo reboot")
        return False  # Need reboot
    except subprocess.CalledProcessError as e:
        logger.error(f"Setup failed: {e}")
        logger.error("Please run manually: cd ~/soap/ePort/scripts && ./setup.sh")
        return False
    except FileNotFoundError:
        logger.error(f"Setup script not found at {script_path}")
        logger.error("Install manually: pip3 install -r requirements.txt")
        return False


def main():
    """Main application loop with comprehensive error handling"""
    
    # Auto-setup if needed
    if not check_and_run_setup():
        return 1
    
    ser = None
    gpio = None
    payment = None
    machine = None
    product_manager = None
    display = None
    
    try:
        # Initialize product manager
        logger.info("Loading product configuration...")
        try:
            product_manager = ProductManager(PRODUCTS_CONFIG_PATH)
            products = product_manager.list_products()
            logger.info(f"Loaded {len(products)} products:")
            for product in products:
                logger.info(f"  - {product.name}: ${product.price_per_unit}/{product.unit}")
        except Exception as e:
            raise VendingMachineError(f"Failed to load products: {e}")
        
        # Initialize display server (required for production)
        if DISPLAY_ENABLED:
            try:
                from .src.display_server import DisplayServer
                logger.info("Starting customer display server...")
                # Pass product info to display
                product_info = [
                    {
                        'id': p.id,
                        'name': p.name,
                        'unit': p.unit,
                        'price_per_unit': p.price_per_unit
                    }
                    for p in products
                ]
                display = DisplayServer(host=DISPLAY_HOST, port=DISPLAY_PORT, products=product_info)
                display.start(background=True)
                logger.info(f"Customer display server started on http://{DISPLAY_HOST}:{DISPLAY_PORT}")
                time.sleep(1)  # Give server time to start
            except Exception as e:
                logger.critical(f"CRITICAL: Failed to start display server: {e}")
                logger.error("Display server is required for production operation")
                logger.error("Install dependencies: pip3 install flask flask-socketio python-socketio")
                raise VendingMachineError(f"Display server initialization failed: {e}")
        else:
            logger.warning("Display server disabled - this should only be used for development/testing")
            logger.warning("Production systems require DISPLAY_ENABLED = True")
            display = None
        
        # Initialize GPIO
        logger.info("Initializing GPIO...")
        gpio = setup_gpio()
        
        # Initialize serial connection
        logger.info("Initializing serial connection...")
        ser = setup_serial_connection()
        
        # Initialize payment protocol handler
        logger.info("Initializing payment protocol handler...")
        payment = EPortProtocol(ser)
        
        # Initialize machine controller with all products
        logger.info("Initializing machine controller...")
        try:
            machine = MachineController(
                gpio=gpio,
                products=products,
                done_button_pin=DONE_BUTTON_PIN
            )
            logger.info("Machine controller initialized successfully")
        except Exception as e:
            raise MachineHardwareError(f"Failed to initialize machine controller: {e}")
        
        logger.info("=" * 60)
        logger.info("Multi-Product Vending Machine Controller Started")
        logger.info(f"Available products: {', '.join(p.name for p in products)}")
        if display:
            logger.info(f"Display: http://{DISPLAY_HOST}:{DISPLAY_PORT}")
        logger.info("=" * 60)
        
        # Main loop - continuously monitor for customers
        consecutive_errors = 0
        
        while True:
            try:
                # STATE 1: Idle - waiting for card
                if display:
                    display.change_state('idle')
                
                # Poll ePort status
                status = safe_status_check(payment)
                
                if status is None:
                    consecutive_errors += 1
                    logger.error(f"Status check failed (consecutive errors: {consecutive_errors})")
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.critical(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                        if display:
                            display.show_error("System error - too many failures", error_code="MAX_ERRORS")
                        break
                    time.sleep(RETRY_DELAY)
                    continue
                
                consecutive_errors = 0  # Reset on success
                logger.debug(f"Status: {status}")
                
                # Check if ePort is disabled (code 6)
                if status == b'6':
                    logger.info("ePort disabled - resetting and requesting authorization")
                    
                    # STATE 2: Authorizing
                    if display:
                        display.change_state('authorizing')
                    
                    if not safe_reset(payment):
                        logger.error("Reset failed - skipping authorization request")
                        time.sleep(RETRY_DELAY)
                        continue
                    
                    time.sleep(POST_RESET_DELAY)
                    
                    # Request authorization
                    if not safe_authorization_request(payment, AUTH_AMOUNT_CENTS):
                        logger.error("Authorization request failed")
                        time.sleep(RETRY_DELAY)
                        continue
                    
                    # Check authorization status
                    time.sleep(AUTHORIZATION_STATUS_CHECK_DELAY)
                    auth_status = safe_status_check(payment)
                    if auth_status:
                        logger.info(f"Auth status: {auth_status}")
                        
                        # Check if declined
                        if auth_status.startswith(b'3'):
                            logger.warning("Authorization declined by bank")
                            if display:
                                display.change_state('declined')
                            time.sleep(5)  # Show declined message
                            continue
                        elif auth_status == b'9':
                            # STATE 3: Ready - show product selection
                            if display:
                                display.change_state('ready')
                            time.sleep(2)  # Show ready screen briefly
                    else:
                        logger.warning("Failed to get auth status")
                        
                # Check if authorization declined (code 3)
                elif status.startswith(b'3'):
                    logger.warning("Authorization declined by bank")
                    if display:
                        display.change_state('declined')
                    time.sleep(DECLINED_CARD_RETRY_DELAY)
                    
                # Check if waiting for transaction result (code 9)
                # This means card was approved and customer can dispense
                elif status == b'9':
                    logger.info("Authorization approved - enabling dispensing")
                    
                    # STATE 4: Dispensing (will be set in handle_dispensing)
                    try:
                        handle_dispensing(machine, payment, product_manager, display)
                    except KeyboardInterrupt:
                        logger.info("Dispensing interrupted by user")
                        raise
                    except Exception as e:
                        logger.error(f"Error during dispensing: {e}")
                        logger.error(traceback.format_exc())
                        
                        # STATE 7: Error
                        if display:
                            display.show_error("Machine error occurred", error_code=str(e)[:50])
                            time.sleep(ERROR_DISPLAY_TIMEOUT)
                        
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


def handle_dispensing(machine: MachineController, payment: EPortProtocol, 
                     product_manager: ProductManager, display: Optional['DisplayServer'] = None):
    """
    Handle the dispensing phase after authorization is approved (Multi-Product)
    
    This function manages the entire dispensing session after a card is authorized.
    The customer can select multiple products, dispense them, and press done when finished.
    
    Flow:
    1. Create TransactionTracker to track all items dispensed
    2. Set up callbacks for flowmeter pulses, product switching, and done button
    3. Enter a loop that monitors product buttons and controls motors
    4. When product button is pressed, select that product and dispense
    5. When done button is pressed, send itemized transaction result
    6. Reset machine state for next customer
    
    Args:
        machine: MachineController instance (handles GPIO, motors, sensors)
        payment: EPortProtocol instance (communicates with ePort card reader)
        product_manager: ProductManager instance (product configurations)
    
    Raises:
        PaymentProtocolError: If transaction completion fails
        MachineHardwareError: If hardware operations fail
    """
    
    # Transaction tracker - records all items dispensed
    transaction = TransactionTracker()
    
    # Track current product being dispensed
    current_product_ounces = 0.0
    last_product_switch_time = 0.0
    
    # Timeout tracking
    session_start_time = time.time()
    last_activity_time = time.time()
    last_button_press_time = time.time()
    warning_displayed = False
    
    # Track if we need to clear active state on button release
    button_was_pressed = False
    
    # Flag to signal that transaction is complete or cancelled
    transaction_complete = False
    
    def on_flowmeter_pulse(ounces: float, price: float):
        """
        Callback for flowmeter pulses - tracks current product dispensing
        
        Args:
            ounces: Ounces dispensed for current product segment
            price: Price for current product segment
        """
        nonlocal current_product_ounces, last_activity_time
        try:
            current_product_ounces = ounces
            product = machine.get_current_product()
            if product:
                logger.debug(f"{product.name}: {ounces:.3f} {product.unit} - ${price:.2f}")
                
                # Update display with current segment only (real-time counter)
                if display:
                    display.update_product(
                        product_id=product.id,
                        product_name=product.name,
                        quantity=ounces,
                        unit=product.unit,
                        price=price,
                        is_active=True
                    )
                    
                    # Update total (transaction total + current segment)
                    total = transaction.get_total() + price
                    display.update_total(total)
            
            last_activity_time = time.time()
        except Exception as e:
            logger.error(f"Error in flowmeter callback: {e}")
    
    def on_product_switch(product):
        """
        Callback when customer switches to a different product
        
        Records the previous product's amount and resets for new product.
        
        Args:
            product: New product being selected
        """
        nonlocal current_product_ounces, last_product_switch_time, last_button_press_time
        
        try:
            # Record previous product if any was dispensed
            prev_product = machine.get_current_product()
            if prev_product and current_product_ounces > 0:
                price = prev_product.calculate_price(current_product_ounces)
                transaction.add_item(
                    product_id=prev_product.id,
                    product_name=prev_product.name,
                    quantity=current_product_ounces,
                    unit=prev_product.unit,
                    price=price
                )
                logger.info(f"Recorded: {prev_product.name} {current_product_ounces:.2f} {prev_product.unit} - ${price:.2f}")
                
                # Update display to show the segment that was just recorded (not active)
                if display:
                    display.update_product(
                        product_id=prev_product.id,
                        product_name=prev_product.name,
                        quantity=current_product_ounces,
                        unit=prev_product.unit,
                        price=price,
                        is_active=False
                    )
            
            # Switch to new product
            logger.info(f"Switching to: {product.name}")
            print(f"\n→ Now dispensing: {product.name}")
            current_product_ounces = 0.0
            last_product_switch_time = time.time()
            last_button_press_time = time.time()
            
        except Exception as e:
            logger.error(f"Error in product switch callback: {e}")
    
    def on_done_button():
        """
        Callback when customer presses "done" - complete multi-product transaction
        
        Records final product, validates transaction, sends itemized result to payment processor.
        """
        nonlocal transaction_complete, current_product_ounces
        
        try:
            # Record final product if any was being dispensed
            current_product = machine.get_current_product()
            if current_product and current_product_ounces > 0:
                price = current_product.calculate_price(current_product_ounces)
                transaction.add_item(
                    product_id=current_product.id,
                    product_name=current_product.name,
                    quantity=current_product_ounces,
                    unit=current_product.unit,
                    price=price
                )
                logger.info(f"Recorded: {current_product.name} {current_product_ounces:.2f} {current_product.unit} - ${price:.2f}")
            
            # Check if anything was dispensed
            if transaction.is_empty():
                logger.warning("Done button pressed but no products dispensed - cancelling transaction")
                machine.reset()
                transaction_complete = True
                return
            
            # Check if too many items (prevent abuse)
            if transaction.get_item_count() > MAX_ITEMS_PER_TRANSACTION:
                logger.error(f"Too many items ({transaction.get_item_count()}) - refusing transaction")
                machine.reset()
                transaction_complete = True
                return
            
            # Get total price
            total_price = transaction.get_total()
            
            # Display itemized transaction to customer (terminal)
            print("\n" + "=" * 40)
            print(transaction.get_summary())
            print("=" * 40)
            
            # Safety check: Prevent charging more than MAX_TRANSACTION_PRICE
            if total_price > MAX_TRANSACTION_PRICE:
                logger.error(f"Price too high: ${total_price:.2f} - refusing transaction")
                machine.reset()
                transaction_complete = True
                return
            
            # Convert to cents for payment processor
            price_cents = transaction.get_total_cents()
            
            # Send transaction result with itemized description
            description = transaction.get_eport_description()
            if not safe_transaction_result(
                payment=payment,
                quantity=transaction.get_item_count(),
                price_cents=price_cents,
                item_id="1",
                description=description
            ):
                raise PaymentProtocolError("Failed to send transaction result")
            
            logger.info(f"Transaction complete: {transaction.get_compact_summary()}")
            
            # Try to get transaction ID
            try:
                transaction_id = payment.get_transaction_id()
                if transaction_id:
                    logger.info(f"Transaction ID: {transaction_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve transaction ID: {e}")
            
            # STATE 5: Complete - Show receipt AFTER payment processing
            if display:
                display.show_receipt(
                    items=transaction.get_items(),
                    total=total_price
                )
                # Show receipt for configured time
                time.sleep(RECEIPT_DISPLAY_TIMEOUT)
            
            # Reset machine
            machine.reset()
            print("\nThank you! Machine ready for next customer\n")
            logger.debug("Machine reset - ready for next customer")
            
            transaction_complete = True
            
        except PaymentProtocolError:
            raise
        except Exception as e:
            logger.error(f"Error in done button callback: {e}")
            logger.error(traceback.format_exc())
            try:
                machine.reset()
            except Exception as reset_error:
                logger.error(f"Error resetting machine after callback error: {reset_error}")
            raise MachineHardwareError(f"Error completing transaction: {e}")
    
    # Start dispensing mode - set up callbacks
    try:
        # STATE 4: Dispensing
        if display:
            display.change_state('dispensing')
        
        machine.start_dispensing(
            flowmeter_callback=on_flowmeter_pulse,
            done_callback=on_done_button,
            product_switch_callback=on_product_switch
        )
        print("\n" + "=" * 40)
        print("SELECT A PRODUCT TO BEGIN")
        products = product_manager.list_products()
        for product in products:
            print(f"  • {product.name} (${product.price_per_unit}/{product.unit})")
        print("Press DONE when finished")
        print("=" * 40 + "\n")
        logger.info("Dispensing enabled - waiting for product selection")
    except Exception as e:
        raise MachineHardwareError(f"Failed to start dispensing mode: {e}")
    
    # Main control loop - monitor product buttons and control motors
    motor_error_count = 0
    
    try:
        while not transaction_complete:
            try:
                current_time = time.time()
                
                # Check for max session timeout (5 minutes total)
                session_duration = current_time - session_start_time
                if session_duration > DISPENSING_MAX_SESSION_TIME:
                    logger.warning(f"Max session time exceeded ({session_duration:.0f}s) - auto-completing")
                    print("\n⏱️  Maximum session time reached - completing transaction...")
                    # Trigger done button callback to complete transaction
                    on_done_button()
                    break
                
                # Update timer on display
                if display:
                    seconds_remaining = int(DISPENSING_MAX_SESSION_TIME - session_duration)
                    inactivity_duration = current_time - last_activity_time
                    warning = inactivity_duration > INACTIVITY_WARNING_TIME
                    display.update_timer(seconds_remaining, warning=warning)
                
                # Check for inactivity timeout
                inactivity_duration = current_time - last_activity_time
                
                # Display warning at 45 seconds of inactivity
                if inactivity_duration > INACTIVITY_WARNING_TIME and not warning_displayed:
                    print(f"\n⚠️  WARNING: {DISPENSING_INACTIVITY_TIMEOUT - inactivity_duration:.0f} seconds until auto-complete")
                    print("   Press DONE or select a product to continue")
                    logger.warning(f"Inactivity warning displayed ({inactivity_duration:.0f}s)")
                    warning_displayed = True
                
                # Auto-complete transaction after 60 seconds of inactivity
                if inactivity_duration > DISPENSING_INACTIVITY_TIMEOUT:
                    logger.warning(f"Inactivity timeout ({inactivity_duration:.0f}s) - auto-completing")
                    print("\n⏱️  Inactivity timeout - completing transaction...")
                    # Trigger done button callback to complete transaction
                    on_done_button()
                    break
                
                # Show waiting screen after WAITING_SCREEN_TIMEOUT seconds of no button press
                # Only show if something has been dispensed or is currently being dispensed
                time_since_last_button = current_time - last_button_press_time
                has_activity = not transaction.is_empty() or current_product_ounces > 0
                if display and has_activity:
                    if time_since_last_button >= WAITING_SCREEN_TIMEOUT:
                        if display.current_state != 'waiting':
                            display.change_state('waiting')
                    else:
                        if display.current_state != 'dispensing':
                            display.change_state('dispensing')
                
                # Check which product button is pressed
                pressed_product = machine.get_pressed_product_button()
                
                if pressed_product:
                    # Product button is pressed - reset inactivity timer and button press time
                    last_activity_time = current_time
                    last_button_press_time = current_time
                    warning_displayed = False  # Reset warning flag
                    button_was_pressed = True
                    
                    current_product = machine.get_current_product()
                    
                    # If switching products, enforce delay and record previous
                    if current_product != pressed_product:
                        time_since_switch = current_time - last_product_switch_time
                        if time_since_switch < PRODUCT_SWITCH_DELAY:
                            # Too soon after last switch, ignore
                            time.sleep(MOTOR_CONTROL_LOOP_DELAY)
                            continue
                        
                        # Switch to new product
                        if machine.select_product(pressed_product):
                            # Product switched - setup flowmeter for new product
                            machine.setup_flowmeter_for_product(pressed_product)
                            # Callback will record previous product
                    
                    # Turn on motor for current product
                    machine.control_motor(True)
                else:
                    # No button pressed - turn off motor and clear active state
                    current_product = machine.get_current_product()
                    if current_product and button_was_pressed:
                        time.sleep(MOTOR_OFF_DEBOUNCE_DELAY)
                        machine.control_motor(False)
                        
                        # Clear active state (turn from GREEN to BLUE)
                        if display and current_product_ounces > 0:
                            display.update_product(
                                product_id=current_product.id,
                                product_name=current_product.name,
                                quantity=current_product_ounces,
                                unit=current_product.unit,
                                price=current_product.calculate_price(current_product_ounces),
                                is_active=False
                            )
                        
                        button_was_pressed = False
                
                # Check if done button was pressed (reset activity timer and button press time)
                if machine.is_done_button_pressed():
                    last_activity_time = current_time
                    last_button_press_time = current_time
                
                motor_error_count = 0
                time.sleep(MOTOR_CONTROL_LOOP_DELAY)
                
            except Exception as e:
                motor_error_count += 1
                logger.warning(f"Error controlling motor (error {motor_error_count}/{MAX_MOTOR_ERRORS}): {e}")
                
                if motor_error_count >= MAX_MOTOR_ERRORS:
                    logger.error("Too many motor control errors - exiting dispensing mode")
                    raise MachineHardwareError("Motor control failed repeatedly")
                
                time.sleep(MOTOR_ERROR_RETRY_DELAY)
            
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
