"""
Product data class
Stores configuration for a single vending machine product
"""

from typing import Optional


class Product:
    """
    Represents a single product in the vending machine
    
    Stores all configuration needed to dispense a product including
    pricing, GPIO pins, and flowmeter calibration.
    """
    
    def __init__(
        self,
        product_id: str,
        name: str,
        price_per_unit: float,
        unit: str,
        motor_pin: int,
        flowmeter_pin: int,
        button_pin: int,
        pulses_per_unit: float,
        description: Optional[str] = None,
        status: str = "AVAILABLE",
        message: str = ""
    ):
        """
        Initialize product configuration
        
        Args:
            product_id: Unique identifier (e.g., "soap_hand")
            name: Display name (e.g., "Hand Soap")
            price_per_unit: Price per unit in dollars (e.g., 0.15)
            unit: Unit type (e.g., "oz", "ml")
            motor_pin: GPIO pin for motor control
            flowmeter_pin: GPIO pin for flowmeter input
            button_pin: GPIO pin for product selection button
            pulses_per_unit: Flowmeter calibration (pulses per unit)
            description: Optional product description
            status: Product availability status (e.g. "AVAILABLE", "OOO")
            message: Optional status message shown to customers
        """
        self.id = product_id
        self.name = name
        self.price_per_unit = price_per_unit
        self.unit = unit
        self.motor_pin = motor_pin
        self.flowmeter_pin = flowmeter_pin
        self.button_pin = button_pin
        self.pulses_per_unit = pulses_per_unit
        self.description = description or ""
        self.status = status or "AVAILABLE"
        self.message = message or ""
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate product configuration"""
        if not self.id:
            raise ValueError("Product ID cannot be empty")
        
        if not self.name:
            raise ValueError(f"Product {self.id}: name cannot be empty")
        
        if self.price_per_unit <= 0:
            raise ValueError(f"Product {self.id}: price must be positive")
        
        if not self.unit:
            raise ValueError(f"Product {self.id}: unit cannot be empty")
        
        if self.motor_pin < 0:
            raise ValueError(f"Product {self.id}: motor_pin must be non-negative")
        
        if self.flowmeter_pin < 0:
            raise ValueError(f"Product {self.id}: flowmeter_pin must be non-negative")
        
        if self.button_pin < 0:
            raise ValueError(f"Product {self.id}: button_pin must be non-negative")
        
        if self.pulses_per_unit <= 0:
            raise ValueError(f"Product {self.id}: pulses_per_unit must be positive")

        if not isinstance(self.status, str):
            raise ValueError(f"Product {self.id}: status must be a string")

        if not isinstance(self.message, str):
            raise ValueError(f"Product {self.id}: message must be a string")

    def is_out_of_order(self) -> bool:
        """Return True when product should be disabled for dispensing."""
        return self.status.strip().upper() == "OOO" or bool(self.message.strip())
    
    def calculate_price(self, quantity: float) -> float:
        """
        Calculate price for given quantity
        
        Args:
            quantity: Amount dispensed in product units
            
        Returns:
            Price in dollars (rounded to 2 decimal places)
        """
        return round(quantity * self.price_per_unit, 2)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"Product(id='{self.id}', name='{self.name}', "
            f"price=${self.price_per_unit}/{self.unit})"
        )
    
    def __str__(self) -> str:
        """Human-readable string"""
        return f"{self.name} (${self.price_per_unit}/{self.unit})"
