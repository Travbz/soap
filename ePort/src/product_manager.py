"""
Product Manager
Loads and manages product configurations from JSON file
"""

import json
import logging
from typing import List, Optional, Dict
from .product import Product

logger = logging.getLogger(__name__)


class ProductManager:
    """
    Manages product configurations and provides product lookup
    
    Loads products from JSON config file and provides methods to
    retrieve products by ID or button pin.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize product manager
        
        Args:
            config_path: Path to products.json configuration file
        """
        self.config_path = config_path
        self.products: Dict[str, Product] = {}
        self._button_pin_map: Dict[int, Product] = {}
        self.load_products()
    
    def load_products(self) -> None:
        """
        Load products from JSON configuration file
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid or has duplicate pins
            json.JSONDecodeError: If JSON is malformed
        """
        logger.info(f"Loading products from {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Products config file not found: {self.config_path}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in products config: {e}")
        
        if 'products' not in config:
            raise ValueError("Products config must have 'products' key")
        
        if not isinstance(config['products'], list):
            raise ValueError("'products' must be a list")
        
        if len(config['products']) == 0:
            raise ValueError("At least one product must be configured")
        
        # Clear existing products
        self.products.clear()
        self._button_pin_map.clear()
        
        # Track pins to detect duplicates
        used_motor_pins = set()
        used_flowmeter_pins = set()
        used_button_pins = set()
        
        # Load each product
        for product_data in config['products']:
            try:
                product = Product(
                    product_id=product_data['id'],
                    name=product_data['name'],
                    price_per_unit=product_data['price_per_unit'],
                    unit=product_data['unit'],
                    motor_pin=product_data['motor_pin'],
                    flowmeter_pin=product_data['flowmeter_pin'],
                    button_pin=product_data['button_pin'],
                    pulses_per_unit=product_data['pulses_per_unit'],
                    description=product_data.get('description', ''),
                    status=product_data.get('status', 'AVAILABLE'),
                    message=product_data.get('message', '')
                )
                
                # Check for duplicate product ID
                if product.id in self.products:
                    raise ValueError(f"Duplicate product ID: {product.id}")
                
                # Check for duplicate GPIO pins
                if product.motor_pin in used_motor_pins:
                    raise ValueError(
                        f"Product {product.id}: motor_pin {product.motor_pin} "
                        f"already used by another product"
                    )
                
                if product.flowmeter_pin in used_flowmeter_pins:
                    raise ValueError(
                        f"Product {product.id}: flowmeter_pin {product.flowmeter_pin} "
                        f"already used by another product"
                    )
                
                if product.button_pin in used_button_pins:
                    raise ValueError(
                        f"Product {product.id}: button_pin {product.button_pin} "
                        f"already used by another product"
                    )
                
                # Add to collections
                self.products[product.id] = product
                self._button_pin_map[product.button_pin] = product
                
                # Track used pins
                used_motor_pins.add(product.motor_pin)
                used_flowmeter_pins.add(product.flowmeter_pin)
                used_button_pins.add(product.button_pin)
                
                logger.info(f"Loaded product: {product}")
                
            except KeyError as e:
                raise ValueError(
                    f"Product missing required field: {e}"
                )
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"Invalid product configuration: {e}"
                )
        
        logger.info(f"Successfully loaded {len(self.products)} products")
    
    def get_product(self, product_id: str) -> Product:
        """
        Get product by ID
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product object
            
        Raises:
            KeyError: If product ID not found
        """
        if product_id not in self.products:
            raise KeyError(f"Product not found: {product_id}")
        return self.products[product_id]
    
    def get_product_by_button_pin(self, pin: int) -> Optional[Product]:
        """
        Get product by button GPIO pin
        
        Args:
            pin: GPIO pin number
            
        Returns:
            Product object if found, None otherwise
        """
        return self._button_pin_map.get(pin)
    
    def list_products(self) -> List[Product]:
        """
        Get list of all products
        
        Returns:
            List of Product objects
        """
        return list(self.products.values())
    
    def get_product_count(self) -> int:
        """Get total number of configured products"""
        return len(self.products)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"ProductManager({len(self.products)} products)"
