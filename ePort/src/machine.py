"""
Machine hardware controller
Handles GPIO, motors, sensors, and dispensing logic
"""

import time
from typing import Callable, Optional, Tuple, Dict, List
from ..config import DONE_BUTTON_SOFTWARE_DEBOUNCE_DELAY, DONE_BUTTON_HARDWARE_DEBOUNCE_MS

# Import Product class for type hints (avoid circular import)
try:
    from .product import Product
except ImportError:
    Product = None


class MachineController:
    """
    Controls vending machine hardware (motors, sensors, buttons)
    
    This class manages all the physical hardware interactions for the vending machine:
    - Motor control (turns pump on/off to dispense product)
    - Flowmeter reading (measures how much product was dispensed)
    - Button monitoring (product buttons to select/dispense, done button to finish)
    - Price calculation (converts flowmeter pulses to ounces and dollars)
    - Product switching (supports multiple products with different motors/sensors)
    
    The class uses GPIO interrupts (callbacks) to respond immediately to hardware events
    like button presses and flowmeter pulses, rather than constantly polling.
    """
    
    def __init__(self, gpio, products: List, done_button_pin: int):
        """
        Initialize machine controller with multi-product support
        
        This sets up all the pins for all products and stores configuration values.
        The actual GPIO pin configuration happens in _setup_gpio().
        
        Args:
            gpio: GPIO module (real RPi.GPIO or mock for testing)
            products: List of Product objects with configuration
            done_button_pin: GPIO pin number for done button (e.g., 27)
        """
        # Store GPIO module
        self.gpio = gpio
        self.done_button_pin = done_button_pin
        
        # Store all products and create button pin mapping
        self.products = products
        self.button_to_product: Dict[int, 'Product'] = {}
        for product in products:
            self.button_to_product[product.button_pin] = product
        
        # Current product being dispensed (set by select_product())
        self.current_product: Optional['Product'] = None
        
        # State variables - track the current dispensing session
        self.pulse_count = 0          # Total flowmeter pulses counted
        self.product_ounces = 0.0     # Calculated ounces dispensed
        self.total_price = 0.0        # Calculated price in dollars
        
        # Callback functions - set by start_dispensing(), called when events occur
        self._flowmeter_callback: Optional[Callable] = None  # Called on each pulse
        self._done_callback: Optional[Callable] = None       # Called when done pressed
        self._product_switch_callback: Optional[Callable] = None  # Called when product changes
        
        # Configure all GPIO pins (set input/output, pull-up resistors, etc.)
        self._setup_gpio()
    
    def _setup_gpio(self):
        """
        Configure GPIO pins for all hardware components (all products)
        
        GPIO pins can be configured as inputs (to read sensors/buttons) or outputs (to control devices).
        Pull-up resistors are used for input pins to ensure a stable HIGH signal when nothing is connected.
        When a button is pressed, it connects the pin to ground (LOW), so we invert the reading.
        """
        # Use BCM (Broadcom) pin numbering - this matches the Raspberry Pi pin layout
        self.gpio.setmode(self.gpio.BCM)
        
        # Setup GPIO pins for each product
        for product in self.products:
            # Flowmeter input: Reads pulses from the flow sensor as product flows
            # PUD_UP means the pin is pulled HIGH when the sensor is not active
            self.gpio.setup(product.flowmeter_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
            
            # Product button input: Customer presses this to select/dispense product
            # When button is NOT pressed: pin reads HIGH (due to pull-up)
            # When button IS pressed: pin reads LOW (connected to ground)
            self.gpio.setup(product.button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
            
            # Motor output: Controls the pump/motor that dispenses the product
            # HIGH = motor ON, LOW = motor OFF
            self.gpio.setup(product.motor_pin, self.gpio.OUT)
            # Ensure motor starts in OFF state
            self.gpio.output(product.motor_pin, self.gpio.LOW)
        
        # Done button input: Customer presses this when finished dispensing
        # Same pull-up behavior as product buttons
        self.gpio.setup(self.done_button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
    
    def select_product(self, product: 'Product') -> bool:
        """
        Select a product for dispensing
        
        Switches the active product, updating motor/flowmeter pins and pricing.
        Should be called when customer presses a different product button.
        
        Args:
            product: Product object to select
            
        Returns:
            True if product was switched, False if already selected
        """
        if self.current_product == product:
            return False  # Already selected
        
        # Turn off motor for previous product (if any)
        if self.current_product:
            self.gpio.output(self.current_product.motor_pin, self.gpio.LOW)
        
        # Notify callback BEFORE switching (so callback can access previous product)
        if self._product_switch_callback:
            self._product_switch_callback(product)
        
        # Switch to new product
        self.current_product = product
        
        return True
    
    def get_current_product(self) -> Optional['Product']:
        """Get currently selected product"""
        return self.current_product
    
    def _on_flowmeter_pulse(self, channel):
        """
        Callback function that runs automatically each time the flowmeter sends a pulse
        
        The flowmeter sends electrical pulses as product flows through it. Each pulse
        represents a small amount of product. We count pulses and convert to ounces,
        then calculate the price based on ounces dispensed.
        
        Uses the current product's calibration and pricing.
        
        Args:
            channel: GPIO pin number (required by RPi.GPIO callback interface, but we don't use it)
        """
        if not self.current_product:
            return  # No product selected, ignore pulse
        
        # Increment the pulse counter - one more pulse detected
        self.pulse_count += 1
        
        # Convert pulses to ounces using current product's calibration factor
        # Example: If pulses_per_unit = 5.4, then 5.4 pulses = 1 ounce
        # Round to 2 decimal places for display (e.g., 2.34 oz)
        self.product_ounces = round(self.pulse_count / self.current_product.pulses_per_unit, 2)
        
        # Calculate total price: ounces × price per ounce
        # Round to 2 decimal places for currency (e.g., $0.35)
        self.total_price = round(self.product_ounces * self.current_product.price_per_unit, 2)
        
        # If a callback function was provided (from main.py), call it with the updated values
        # This allows the main program to log or display the current dispense info
        if self._flowmeter_callback:
            self._flowmeter_callback(self.product_ounces, self.total_price)
    
    def start_dispensing(self, flowmeter_callback: Optional[Callable] = None,
                        done_callback: Optional[Callable] = None,
                        product_switch_callback: Optional[Callable] = None):
        """
        Start dispensing mode with callbacks
        
        This function prepares the machine for a customer to dispense products. It resets
        all counters and sets up interrupt handlers (callbacks) that respond to hardware events.
        
        Note: Flowmeter event detection is set up when a product is first selected,
        not here, since each product has its own flowmeter pin.
        
        Args:
            flowmeter_callback: Function to call each time the flowmeter pulses (receives ounces, price)
            done_callback: Function to call when the customer presses the "done" button
            product_switch_callback: Function to call when product is switched
        """
        # Reset all counters - start fresh for this transaction
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        self.current_product = None
        
        # Store the callback functions so we can call them when events happen
        self._flowmeter_callback = flowmeter_callback
        self._done_callback = done_callback
        self._product_switch_callback = product_switch_callback
        
        # Remove any existing event detection before adding new ones
        # This prevents "Conflicting edge detection already enabled" errors
        for product in self.products:
            try:
                self.gpio.remove_event_detect(product.flowmeter_pin)
            except RuntimeError:
                pass  # No event detection was set up, that's fine
        
        try:
            self.gpio.remove_event_detect(self.done_button_pin)
        except RuntimeError:
            pass  # No event detection was set up, that's fine
        
        # Setup interrupt handler for done button
        # FALLING edge means the signal goes from HIGH to LOW (button pressed, connects to ground)
        # bouncetime prevents false triggers from electrical "bounce" when a mechanical button is pressed
        self.gpio.add_event_detect(
            self.done_button_pin, 
            self.gpio.FALLING,  # Trigger on falling edge (HIGH → LOW transition)
            callback=lambda x: self._on_done_button(),  # Call our handler function
            bouncetime=DONE_BUTTON_HARDWARE_DEBOUNCE_MS  # Hardware debounce from config
        )
    
    def _on_done_button(self):
        """
        Handle done button press event
        
        This function is called automatically by the GPIO interrupt handler when the
        done button is pressed. It triggers the callback function that was passed to
        start_dispensing(), which handles the transaction completion logic.
        
        Includes software debouncing: checks if button is actually pressed to prevent
        false triggers from electrical noise.
        """
        # Software debouncing: verify button is actually pressed (not just noise)
        # Wait a tiny bit then check again to filter out brief spikes
        time.sleep(DONE_BUTTON_SOFTWARE_DEBOUNCE_DELAY)
        if not self.is_done_button_pressed():
            # Button not actually pressed - false trigger, ignore it
            return
        
        # Button is actually pressed - trigger the callback
        if self._done_callback:
            self._done_callback()
    
    def control_motor(self, state: bool):
        """
        Control motor on/off for currently selected product
        
        The motor controls the pump that dispenses the product. When the customer
        presses and holds the product button, the motor runs. When they release it,
        the motor stops.
        
        Args:
            state: True to turn motor ON (HIGH), False to turn motor OFF (LOW)
        """
        if not self.current_product:
            return  # No product selected
        
        # GPIO.HIGH = 3.3V = motor ON, GPIO.LOW = 0V = motor OFF
        self.gpio.output(self.current_product.motor_pin, self.gpio.HIGH if state else self.gpio.LOW)
    
    def is_product_button_pressed(self, product: Optional['Product'] = None) -> bool:
        """
        Check if a product button is currently pressed
        
        IMPORTANT: We invert the GPIO reading because of pull-up resistor behavior.
        - When button is NOT pressed: GPIO reads HIGH (due to pull-up resistor)
        - When button IS pressed: GPIO reads LOW (button connects pin to ground)
        - So: gpio.input() returns False when pressed, True when not pressed
        - We invert it so this function returns True when pressed (more intuitive)
        
        Args:
            product: Product to check button for (defaults to current product)
        
        Returns:
            True if button is pressed, False if not pressed
        """
        if product is None:
            product = self.current_product
        
        if not product:
            return False
        
        # Invert because pull-up makes pressed = LOW (False), not pressed = HIGH (True)
        return not self.gpio.input(product.button_pin)
    
    def get_pressed_product_button(self) -> Optional['Product']:
        """
        Check all product buttons and return which one is pressed
        
        Returns:
            Product whose button is pressed, or None if no button pressed
        """
        for product in self.products:
            if not self.gpio.input(product.button_pin):  # Inverted - LOW means pressed
                return product
        return None
    
    def is_done_button_pressed(self) -> bool:
        """
        Check if done button is currently pressed
        
        Same pull-up inversion logic as is_product_button_pressed()
        
        Returns:
            True if button is pressed, False if not pressed
        """
        return not self.gpio.input(self.done_button_pin)  # Inverted because of pull-up
    
    def get_dispense_info(self) -> Tuple[float, float]:
        """
        Get current dispense information for the current transaction
        
        Returns the amount of product dispensed (in ounces) and the calculated price
        based on the flowmeter pulses counted so far. Used when the customer presses
        "done" to complete the transaction.
        
        Returns:
            Tuple of (ounces_dispensed, price_in_dollars)
            Example: (2.34, 0.35) means 2.34 ounces dispensed, $0.35 charged
        """
        return self.product_ounces, self.total_price
    
    def setup_flowmeter_for_product(self, product: 'Product'):
        """
        Setup flowmeter event detection for a specific product
        
        Called when customer starts dispensing a product.
        Each product has its own flowmeter pin.
        
        Args:
            product: Product to setup flowmeter for
        """
        # Remove existing detection for this product's flowmeter
        try:
            self.gpio.remove_event_detect(product.flowmeter_pin)
        except RuntimeError:
            pass
        
        # Setup interrupt handler for this product's flowmeter
        self.gpio.add_event_detect(
            product.flowmeter_pin,
            self.gpio.RISING,  # Trigger on rising edge (LOW → HIGH transition)
            callback=self._on_flowmeter_pulse
        )
    
    def reset(self):
        """
        Reset all dispense counters and callbacks
        
        This should be called after a transaction is complete to prepare the machine
        for the next customer. Clears all the state variables and removes callback
        references so the machine is ready for a new dispensing session.
        """
        # Turn off all motors
        for product in self.products:
            self.gpio.output(product.motor_pin, self.gpio.LOW)
        
        # Remove event detection to clean up GPIO state
        # This prevents conflicts when start_dispensing() is called again
        for product in self.products:
            try:
                self.gpio.remove_event_detect(product.flowmeter_pin)
            except RuntimeError:
                pass  # No event detection was set up, that's fine
        
        try:
            self.gpio.remove_event_detect(self.done_button_pin)
        except RuntimeError:
            pass  # No event detection was set up, that's fine
        
        # Reset all counters to zero
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        self.current_product = None
        
        # Clear callback references (no longer needed, transaction is done)
        self._flowmeter_callback = None
        self._done_callback = None
        self._product_switch_callback = None