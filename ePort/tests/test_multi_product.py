"""
Unit tests for multi-product system
Tests Product, ProductManager, and TransactionTracker classes
"""

import os
import json
import tempfile
import unittest
from ePort.src.product import Product
from ePort.src.product_manager import ProductManager
from ePort.src.transaction_tracker import TransactionTracker


class TestProduct(unittest.TestCase):
    """Test Product class"""
    
    def test_product_creation(self):
        """Test creating a valid product"""
        product = Product(
            product_id="soap_hand",
            name="Hand Soap",
            price_per_unit=0.15,
            unit="oz",
            motor_pin=17,
            flowmeter_pin=24,
            button_pin=4,
            pulses_per_unit=5.4,
            description="Gentle hand wash"
        )
        
        self.assertEqual(product.id, "soap_hand")
        self.assertEqual(product.name, "Hand Soap")
        self.assertEqual(product.price_per_unit, 0.15)
        self.assertEqual(product.unit, "oz")
        self.assertEqual(product.motor_pin, 17)
        self.assertEqual(product.flowmeter_pin, 24)
        self.assertEqual(product.button_pin, 4)
        self.assertEqual(product.pulses_per_unit, 5.4)
        self.assertEqual(product.description, "Gentle hand wash")
    
    def test_product_calculate_price(self):
        """Test price calculation"""
        product = Product(
            product_id="soap",
            name="Soap",
            price_per_unit=0.15,
            unit="oz",
            motor_pin=17,
            flowmeter_pin=24,
            button_pin=4,
            pulses_per_unit=5.4
        )
        
        # Test various quantities
        self.assertEqual(product.calculate_price(1.0), 0.15)
        self.assertEqual(product.calculate_price(2.5), 0.38)  # Rounded
        self.assertEqual(product.calculate_price(10.0), 1.50)
    
    def test_product_validation_empty_id(self):
        """Test validation fails for empty ID"""
        with self.assertRaises(ValueError) as context:
            Product(
                product_id="",
                name="Soap",
                price_per_unit=0.15,
                unit="oz",
                motor_pin=17,
                flowmeter_pin=24,
                button_pin=4,
                pulses_per_unit=5.4
            )
        self.assertIn("ID cannot be empty", str(context.exception))
    
    def test_product_validation_negative_price(self):
        """Test validation fails for negative price"""
        with self.assertRaises(ValueError) as context:
            Product(
                product_id="soap",
                name="Soap",
                price_per_unit=-0.15,
                unit="oz",
                motor_pin=17,
                flowmeter_pin=24,
                button_pin=4,
                pulses_per_unit=5.4
            )
        self.assertIn("price must be positive", str(context.exception))
    
    def test_product_validation_negative_pulses(self):
        """Test validation fails for negative pulses_per_unit"""
        with self.assertRaises(ValueError) as context:
            Product(
                product_id="soap",
                name="Soap",
                price_per_unit=0.15,
                unit="oz",
                motor_pin=17,
                flowmeter_pin=24,
                button_pin=4,
                pulses_per_unit=-5.4
            )
        self.assertIn("pulses_per_unit must be positive", str(context.exception))


class TestProductManager(unittest.TestCase):
    """Test ProductManager class"""
    
    def setUp(self):
        """Create temporary config file for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "products.json")
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def create_config(self, products):
        """Helper to create config file"""
        with open(self.config_path, 'w') as f:
            json.dump({"products": products}, f)
    
    def test_load_single_product(self):
        """Test loading single product"""
        self.create_config([{
            "id": "soap_hand",
            "name": "Hand Soap",
            "price_per_unit": 0.15,
            "unit": "oz",
            "motor_pin": 17,
            "flowmeter_pin": 24,
            "button_pin": 4,
            "pulses_per_unit": 5.4
        }])
        
        manager = ProductManager(self.config_path)
        
        self.assertEqual(manager.get_product_count(), 1)
        product = manager.get_product("soap_hand")
        self.assertEqual(product.name, "Hand Soap")
    
    def test_load_multiple_products(self):
        """Test loading multiple products"""
        self.create_config([
            {
                "id": "soap_hand",
                "name": "Hand Soap",
                "price_per_unit": 0.15,
                "unit": "oz",
                "motor_pin": 17,
                "flowmeter_pin": 24,
                "button_pin": 4,
                "pulses_per_unit": 5.4
            },
            {
                "id": "soap_dish",
                "name": "Dish Soap",
                "price_per_unit": 0.12,
                "unit": "oz",
                "motor_pin": 18,
                "flowmeter_pin": 25,
                "button_pin": 23,
                "pulses_per_unit": 5.2
            }
        ])
        
        manager = ProductManager(self.config_path)
        
        self.assertEqual(manager.get_product_count(), 2)
        self.assertEqual(manager.get_product("soap_hand").name, "Hand Soap")
        self.assertEqual(manager.get_product("soap_dish").name, "Dish Soap")
    
    def test_get_product_by_button_pin(self):
        """Test retrieving product by button pin"""
        self.create_config([{
            "id": "soap_hand",
            "name": "Hand Soap",
            "price_per_unit": 0.15,
            "unit": "oz",
            "motor_pin": 17,
            "flowmeter_pin": 24,
            "button_pin": 4,
            "pulses_per_unit": 5.4
        }])
        
        manager = ProductManager(self.config_path)
        product = manager.get_product_by_button_pin(4)
        
        self.assertIsNotNone(product)
        self.assertEqual(product.id, "soap_hand")
    
    def test_get_product_by_invalid_button_pin(self):
        """Test retrieving product with non-existent button pin"""
        self.create_config([{
            "id": "soap_hand",
            "name": "Hand Soap",
            "price_per_unit": 0.15,
            "unit": "oz",
            "motor_pin": 17,
            "flowmeter_pin": 24,
            "button_pin": 4,
            "pulses_per_unit": 5.4
        }])
        
        manager = ProductManager(self.config_path)
        product = manager.get_product_by_button_pin(99)
        
        self.assertIsNone(product)
    
    def test_duplicate_product_id(self):
        """Test error on duplicate product ID"""
        self.create_config([
            {
                "id": "soap",
                "name": "Hand Soap",
                "price_per_unit": 0.15,
                "unit": "oz",
                "motor_pin": 17,
                "flowmeter_pin": 24,
                "button_pin": 4,
                "pulses_per_unit": 5.4
            },
            {
                "id": "soap",
                "name": "Dish Soap",
                "price_per_unit": 0.12,
                "unit": "oz",
                "motor_pin": 18,
                "flowmeter_pin": 25,
                "button_pin": 23,
                "pulses_per_unit": 5.2
            }
        ])
        
        with self.assertRaises(ValueError) as context:
            ProductManager(self.config_path)
        self.assertIn("Duplicate product ID", str(context.exception))
    
    def test_duplicate_motor_pin(self):
        """Test error on duplicate motor pin"""
        self.create_config([
            {
                "id": "soap_hand",
                "name": "Hand Soap",
                "price_per_unit": 0.15,
                "unit": "oz",
                "motor_pin": 17,
                "flowmeter_pin": 24,
                "button_pin": 4,
                "pulses_per_unit": 5.4
            },
            {
                "id": "soap_dish",
                "name": "Dish Soap",
                "price_per_unit": 0.12,
                "unit": "oz",
                "motor_pin": 17,  # Duplicate!
                "flowmeter_pin": 25,
                "button_pin": 23,
                "pulses_per_unit": 5.2
            }
        ])
        
        with self.assertRaises(ValueError) as context:
            ProductManager(self.config_path)
        self.assertIn("motor_pin", str(context.exception))
        self.assertIn("already used", str(context.exception))
    
    def test_missing_config_file(self):
        """Test error when config file doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            ProductManager("/nonexistent/path/products.json")
    
    def test_invalid_json(self):
        """Test error on malformed JSON"""
        with open(self.config_path, 'w') as f:
            f.write("{invalid json")
        
        with self.assertRaises(ValueError) as context:
            ProductManager(self.config_path)
        self.assertIn("Invalid JSON", str(context.exception))
    
    def test_missing_products_key(self):
        """Test error when 'products' key is missing"""
        with open(self.config_path, 'w') as f:
            json.dump({"items": []}, f)
        
        with self.assertRaises(ValueError) as context:
            ProductManager(self.config_path)
        self.assertIn("'products' key", str(context.exception))
    
    def test_empty_products_list(self):
        """Test error when products list is empty"""
        self.create_config([])
        
        with self.assertRaises(ValueError) as context:
            ProductManager(self.config_path)
        self.assertIn("At least one product", str(context.exception))


class TestTransactionTracker(unittest.TestCase):
    """Test TransactionTracker class"""
    
    def test_empty_transaction(self):
        """Test empty transaction"""
        tracker = TransactionTracker()
        
        self.assertTrue(tracker.is_empty())
        self.assertEqual(tracker.get_item_count(), 0)
        self.assertEqual(tracker.get_total(), 0.0)
        self.assertEqual(tracker.get_total_cents(), 0)
    
    def test_add_single_item(self):
        """Test adding single item"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        
        self.assertFalse(tracker.is_empty())
        self.assertEqual(tracker.get_item_count(), 1)
        self.assertEqual(tracker.get_total(), 0.38)
        self.assertEqual(tracker.get_total_cents(), 38)
    
    def test_add_multiple_items(self):
        """Test adding multiple items"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        tracker.add_item("soap_dish", "Dish Soap", 3.2, "oz", 0.38)
        
        self.assertEqual(tracker.get_item_count(), 2)
        self.assertEqual(tracker.get_total(), 0.76)
        self.assertEqual(tracker.get_total_cents(), 76)
    
    def test_get_items(self):
        """Test retrieving items list"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        
        items = tracker.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product_id"], "soap_hand")
        self.assertEqual(items[0]["product_name"], "Hand Soap")
        self.assertEqual(items[0]["quantity"], 2.5)
        self.assertEqual(items[0]["unit"], "oz")
        self.assertEqual(items[0]["price"], 0.38)
    
    def test_get_summary(self):
        """Test transaction summary generation"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        tracker.add_item("soap_dish", "Dish Soap", 3.2, "oz", 0.38)
        
        summary = tracker.get_summary()
        self.assertIn("Hand Soap", summary)
        self.assertIn("Dish Soap", summary)
        self.assertIn("$0.76", summary)
    
    def test_get_compact_summary(self):
        """Test compact summary"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        tracker.add_item("soap_dish", "Dish Soap", 3.2, "oz", 0.38)
        
        summary = tracker.get_compact_summary()
        self.assertIn("2 items", summary)
        self.assertIn("$0.76", summary)
    
    def test_get_eport_description_single_item(self):
        """Test ePort description for single item"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        
        desc = tracker.get_eport_description()
        self.assertIn("2.50", desc)
        self.assertIn("oz", desc)
        self.assertLessEqual(len(desc), 30)  # Must fit ePort limit
    
    def test_get_eport_description_multiple_items(self):
        """Test ePort description for multiple items"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        tracker.add_item("soap_dish", "Dish Soap", 3.2, "oz", 0.38)
        
        desc = tracker.get_eport_description()
        self.assertIn("2 items", desc)
        self.assertLessEqual(len(desc), 30)  # Must fit ePort limit
    
    def test_reset(self):
        """Test transaction reset"""
        tracker = TransactionTracker()
        tracker.add_item("soap_hand", "Hand Soap", 2.5, "oz", 0.38)
        
        self.assertFalse(tracker.is_empty())
        
        tracker.reset()
        
        self.assertTrue(tracker.is_empty())
        self.assertEqual(tracker.get_total(), 0.0)
        self.assertEqual(tracker.get_item_count(), 0)
    
    def test_price_rounding(self):
        """Test price rounding to 2 decimal places"""
        tracker = TransactionTracker()
        tracker.add_item("soap", "Soap", 1.0, "oz", 0.33)
        tracker.add_item("soap", "Soap", 1.0, "oz", 0.33)
        tracker.add_item("soap", "Soap", 1.0, "oz", 0.34)
        
        # 0.33 + 0.33 + 0.34 = 1.00
        self.assertEqual(tracker.get_total(), 1.00)


def run_all_tests():
    """Run all multi-product tests"""
    print("=" * 60)
    print("Testing Multi-Product System")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestProduct))
    suite.addTests(loader.loadTestsFromTestCase(TestProductManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTransactionTracker))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Results: {result.testsRun} tests, "
          f"{len(result.failures)} failures, "
          f"{len(result.errors)} errors")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
