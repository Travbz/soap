"""
Machine hardware controller
Handles GPIO, motors, sensors, and dispensing logic
"""

import time
from typing import Callable, Optional


class MachineController:
    """Controls vending machine hardware (motors, sensors, buttons)"""
    
    def __init__(self, gpio, motor_pin: int, flowmeter_pin: int, 
                 product_button_pin: int, done_button_pin: int,
                 price_per_ounce: float, pulses_per_ounce: float,
                 product_unit: str):
        """
        Initialize machine controller
        
        Args:
            gpio: GPIO module (real RPi.GPIO or mock)
            motor_pin: GPIO pin for motor control
            flowmeter_pin: GPIO pin for flowmeter input
            product_button_pin: GPIO pin for product selection button
            done_button_pin: GPIO pin for done button
            price_per_ounce: Price per ounce in dollars
            pulses_per_ounce: Flowmeter calibration (pulses per ounce)
            product_unit: Product unit description
        """
        self.gpio = gpio
        self.motor_pin = motor_pin
        self.flowmeter_pin = flowmeter_pin
        self.product_button_pin = product_button_pin
        self.done_button_pin = done_button_pin
        self.price_per_ounce = price_per_ounce
        self.pulses_per_ounce = pulses_per_ounce
        self.product_unit = product_unit
        
        # State variables
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        self._flowmeter_callback: Optional[Callable] = None
        self._done_callback: Optional[Callable] = None
        
        # Setup GPIO
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Configure GPIO pins"""
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.flowmeter_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        self.gpio.setup(self.product_button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
        self.gpio.setup(self.motor_pin, self.gpio.OUT)
        self.gpio.setup(self.done_button_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
    
    def _on_flowmeter_pulse(self, channel):
        """Callback for flowmeter pulses"""
        self.pulse_count += 1
        self.product_ounces = round(self.pulse_count / self.pulses_per_ounce, 2)
        self.total_price = round(self.product_ounces * self.price_per_ounce, 2)
        
        if self._flowmeter_callback:
            self._flowmeter_callback(self.product_ounces, self.total_price)
    
    def start_dispensing(self, flowmeter_callback: Optional[Callable] = None,
                        done_callback: Optional[Callable] = None):
        """
        Start dispensing mode with callbacks
        
        Args:
            flowmeter_callback: Called on each flowmeter pulse (ounces, price)
            done_callback: Called when done button is pressed
        """
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        self._flowmeter_callback = flowmeter_callback
        self._done_callback = done_callback
        
        # Setup event detection
        self.gpio.add_event_detect(
            self.flowmeter_pin, 
            self.gpio.RISING, 
            callback=self._on_flowmeter_pulse
        )
        self.gpio.add_event_detect(
            self.done_button_pin, 
            self.gpio.FALLING, 
            callback=lambda x: self._on_done_button(),
            bouncetime=300
        )
    
    def _on_done_button(self):
        """Handle done button press"""
        if self._done_callback:
            self._done_callback()
    
    def control_motor(self, state: bool):
        """
        Control motor on/off
        
        Args:
            state: True to turn on, False to turn off
        """
        self.gpio.output(self.motor_pin, self.gpio.HIGH if state else self.gpio.LOW)
    
    def is_product_button_pressed(self) -> bool:
        """Check if product button is pressed"""
        return not self.gpio.input(self.product_button_pin)  # Inverted because of pull-up
    
    def is_done_button_pressed(self) -> bool:
        """Check if done button is pressed"""
        return not self.gpio.input(self.done_button_pin)  # Inverted because of pull-up
    
    def get_dispense_info(self) -> tuple[float, float]:
        """
        Get current dispense information
        
        Returns:
            Tuple of (ounces, price_in_dollars)
        """
        return self.product_ounces, self.total_price
    
    def reset(self):
        """Reset dispense counters"""
        self.pulse_count = 0
        self.product_ounces = 0.0
        self.total_price = 0.0
        self._flowmeter_callback = None
        self._done_callback = None
