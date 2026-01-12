"""
Machine hardware controller
Handles GPIO, motors, sensors, and dispensing logic
"""

import time
from typing import Callable, Optional, Tuple


class MachineController:
    """
    Controls vending machine hardware (motors, sensors, buttons)
    
    This class manages all the physical hardware interactions for the vending machine:
    - Motor control (turns pump on/off to dispense product)
    - Flowmeter reading (measures how much product was dispensed)
    - Button monitoring (product button to dispense, done button to finish)
    - Price calculation (converts flowmeter pulses to ounces and dollars)
    
    The class uses GPIO interrupts (callbacks) to respond immediately to hardware events
    like button presses and flowmeter pulses, rather than constantly polling.
    """
    
    def __init__(self, gpio, motor_pin: int, flowmeter_pin: int, 
                 product_button_pin: int, done_button_pin: int,
                 price_per_ounce: float, pulses_per_ounce: float,
                 product_unit: str):
        """
        Initialize machine controller with hardware configuration
        
        This sets up all the pins and stores configuration values. The actual GPIO
        pin configuration happens in _setup_gpio().
        
        Args:
            gpio: GPIO module (real RPi.GPIO or mock for testing)
            motor_pin: GPIO pin number for motor control (e.g., 17)
            flowmeter_pin: GPIO pin number for flowmeter input (e.g., 24)
            product_button_pin: GPIO pin number for product button (e.g., 4)
            done_button_pin: GPIO pin number for done button (e.g., 27)
            price_per_ounce: Price per ounce in dollars (e.g., 0.15 = $0.15/oz)
            pulses_per_ounce: Flowmeter calibration factor (e.g., 5.4 = 5.4 pulses per ounce)
            product_unit: Product unit description (e.g., "oz hand wash")
        """
        # Store GPIO module and pin numbers for later use
        self.gpio = gpio
        self.motor_pin = motor_pin
        self.flowmeter_pin = flowmeter_pin
        self.product_button_pin = product_button_pin
        self.done_button_pin = done_button_pin
        
        # Store pricing and calibration configuration
        self.price_per_ounce = price_per_ounce
        self.pulses_per_ounce = pulses_per_ounce
        self.product_unit = product_unit
        
        # State variables - track the current dispensing session
        self.pulse_count = 0          # Total flowmeter pulses counted
        self.product_ounces = 0.0     # Calculated ounces dispensed
        self.total_price = 0.0        # Calculated price in dollars
        
        # Callback functions - set by start_dispensing(), called when events occur
        self._flowmeter_callback: Optional[Callable] = None  # Called on each pulse
        self._done_callback: Optional[Callable] = None       # Called when done pressed
        
        # Configure all GPIO pins (set input/output, pull-up resistors, etc.)
        self._setup_gpio()
    
    def _setup_gpio(self):
        """
        Configure GPIO pins for all hardware components
        
        GPIO pins can be configured as inputs (to read sensors/buttons) or outputs (to control devices).
        Pull-up resistors are used for input pins to ensure a stable HIGH signal when nothing is connected.
        When a button is pressed, it connects the pin to ground (LOW), so we invert the reading.
        """
        # Use BCM (Broadcom) pin numbering - this matches the Raspberry Pi pin layout
        self.gpio.setmode(self.gpio.BCM)
        
        # Flowmeter input: Reads pulses from the flow sensor as product flows
        # PUD_UP means the pin is pulled HIGH when the button/sensor is not active
        self.gpio.setup(self.flowmeter_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        
        # Product button input: Customer presses this to dispense product
        # When button is NOT pressed: pin reads HIGH (due to pull-up)
        # When button IS pressed: pin reads LOW (connected to ground)
        self.gpio.setup(self.product_button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        
        # Motor output: Controls the pump/motor that dispenses the product
        # HIGH = motor ON, LOW = motor OFF
        self.gpio.setup(self.motor_pin, self.gpio.OUT)
        
        # Done button input: Customer presses this when finished dispensing
        # Same pull-up behavior as product button
        self.gpio.setup(self.done_button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
    
    def _on_flowmeter_pulse(self, channel):
        """
        Callback function that runs automatically each time the flowmeter sends a pulse
        
        The flowmeter sends electrical pulses as product flows through it. Each pulse
        represents a small amount of product. We count pulses and convert to ounces,
        then calculate the price based on ounces dispensed.
        
        Args:
            channel: GPIO pin number (required by RPi.GPIO callback interface, but we don't use it)
        """
        # Increment the pulse counter - one more pulse detected
        self.pulse_count += 1
        
        # Convert pulses to ounces using calibration factor
        # Example: If pulses_per_ounce = 5.4, then 5.4 pulses = 1 ounce
        # Round to 2 decimal places for display (e.g., 2.34 oz)
        self.product_ounces = round(self.pulse_count / self.pulses_per_ounce, 2)
        
        # Calculate total price: ounces × price per ounce
        # Round to 2 decimal places for currency (e.g., $0.35)
        self.total_price = round(self.product_ounces * self.price_per_ounce, 2)
        
        # If a callback function was provided (from main.py), call it with the updated values
        # This allows the main program to log or display the current dispense info
        if self._flowmeter_callback:
            self._flowmeter_callback(self.product_ounces, self.total_price)
    
    def start_dispensing(self, flowmeter_callback: Optional[Callable] = None,
                        done_callback: Optional[Callable] = None):
        """
        Start dispensing mode with callbacks
        
        This function prepares the machine for a customer to dispense product. It resets
        all counters and sets up interrupt handlers (callbacks) that respond to hardware events.
        
        Args:
            flowmeter_callback: Function to call each time the flowmeter pulses (receives ounces, price)
            done_callback: Function to call when the customer presses the "done" button
        """
        # Reset all counters - start fresh for this transaction
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        
        # Store the callback functions so we can call them when events happen
        self._flowmeter_callback = flowmeter_callback
        self._done_callback = done_callback
        
        # Setup interrupt handler for flowmeter pulses
        # RISING edge means the signal goes from LOW to HIGH (a pulse)
        # When a pulse is detected, automatically call self._on_flowmeter_pulse()
        self.gpio.add_event_detect(
            self.flowmeter_pin, 
            self.gpio.RISING,  # Trigger on rising edge (LOW → HIGH transition)
            callback=self._on_flowmeter_pulse
        )
        
        # Setup interrupt handler for done button
        # FALLING edge means the signal goes from HIGH to LOW (button pressed, connects to ground)
        # bouncetime=300 means ignore any changes for 300ms after the first detection
        #   This prevents false triggers from electrical "bounce" when a mechanical button is pressed
        self.gpio.add_event_detect(
            self.done_button_pin, 
            self.gpio.FALLING,  # Trigger on falling edge (HIGH → LOW transition)
            callback=lambda x: self._on_done_button(),  # Call our handler function
            bouncetime=300  # Ignore changes for 300ms (prevents button bounce false triggers)
        )
    
    def _on_done_button(self):
        """
        Handle done button press event
        
        This function is called automatically by the GPIO interrupt handler when the
        done button is pressed. It triggers the callback function that was passed to
        start_dispensing(), which handles the transaction completion logic.
        """
        if self._done_callback:
            self._done_callback()
    
    def control_motor(self, state: bool):
        """
        Control motor on/off
        
        The motor controls the pump that dispenses the product. When the customer
        presses and holds the product button, the motor runs. When they release it,
        the motor stops.
        
        Args:
            state: True to turn motor ON (HIGH), False to turn motor OFF (LOW)
        """
        # GPIO.HIGH = 3.3V = motor ON, GPIO.LOW = 0V = motor OFF
        self.gpio.output(self.motor_pin, self.gpio.HIGH if state else self.gpio.LOW)
    
    def is_product_button_pressed(self) -> bool:
        """
        Check if product button is currently pressed
        
        IMPORTANT: We invert the GPIO reading because of pull-up resistor behavior.
        - When button is NOT pressed: GPIO reads HIGH (due to pull-up resistor)
        - When button IS pressed: GPIO reads LOW (button connects pin to ground)
        - So: gpio.input() returns False when pressed, True when not pressed
        - We invert it so this function returns True when pressed (more intuitive)
        
        Returns:
            True if button is pressed, False if not pressed
        """
        # Invert because pull-up makes pressed = LOW (False), not pressed = HIGH (True)
        return not self.gpio.input(self.product_button_pin)
    
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
    
    def reset(self):
        """
        Reset all dispense counters and callbacks
        
        This should be called after a transaction is complete to prepare the machine
        for the next customer. Clears all the state variables and removes callback
        references so the machine is ready for a new dispensing session.
        """
        # Reset all counters to zero
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        
        # Clear callback references (no longer needed, transaction is done)
        self._flowmeter_callback = None
        self._done_callback = None
