"""
Test script for display server

Run this to test the display without the full vending machine system.
"""

import time
import sys
from ePort.src.display_server import DisplayServer

def main():
    print("Starting display server test...")
    
    # Initialize and start server
    display = DisplayServer(host='localhost', port=5000)
    display.start(background=True)
    
    print(f"Display server running on http://localhost:5000")
    print("Open in browser: http://localhost:5000")
    print("\nRunning through all states...\n")
    
    time.sleep(2)
    
    # Test state transitions
    print("1. Idle state (swipe card)")
    display.change_state('idle')
    time.sleep(3)
    
    print("2. Authorizing payment...")
    display.change_state('authorizing')
    time.sleep(3)
    
    print("3. Ready - product selection")
    display.change_state('ready')
    time.sleep(3)
    
    print("4. Dispensing - live counters")
    display.change_state('dispensing')
    time.sleep(1)
    
    # Simulate dispensing hand soap
    print("   Dispensing Hand Soap...")
    for i in range(1, 8):
        qty = i * 1.2
        price = qty * 0.15
        display.update_product(
            product_id='soap_hand',
            product_name='Hand Soap',
            quantity=qty,
            unit='oz',
            price=price,
            is_active=True
        )
        display.update_total(price)
        time.sleep(0.5)
    
    # Switch to dish soap
    print("   Switching to Dish Soap...")
    display.update_product(
        product_id='soap_hand',
        product_name='Hand Soap',
        quantity=8.4,
        unit='oz',
        price=1.26,
        is_active=False
    )
    
    for i in range(1, 6):
        qty = i * 1.5
        price = qty * 0.12
        display.update_product(
            product_id='soap_dish',
            product_name='Dish Soap',
            quantity=qty,
            unit='oz',
            price=price,
            is_active=True
        )
        display.update_total(1.26 + price)
        time.sleep(0.5)
    
    print("   Switching to Laundry...")
    display.update_product(
        product_id='soap_dish',
        product_name='Dish Soap',
        quantity=7.5,
        unit='oz',
        price=0.90,
        is_active=False
    )
    
    for i in range(1, 5):
        qty = i * 2.0
        price = qty * 0.10
        display.update_product(
            product_id='soap_laundry',
            product_name='Laundry',
            quantity=qty,
            unit='oz',
            price=price,
            is_active=True
        )
        display.update_total(1.26 + 0.90 + price)
        time.sleep(0.5)
    
    time.sleep(2)
    
    print("5. Complete - showing receipt")
    display.show_receipt(
        items=[
            {'product_name': 'Hand Soap', 'quantity': 8.4, 'unit': 'oz', 'price': 1.26},
            {'product_name': 'Dish Soap', 'quantity': 7.5, 'unit': 'oz', 'price': 0.90},
            {'product_name': 'Laundry', 'quantity': 8.0, 'unit': 'oz', 'price': 0.80}
        ],
        total=2.96
    )
    time.sleep(5)
    
    print("6. Declined card")
    display.change_state('declined')
    time.sleep(3)
    
    print("7. Error state")
    display.show_error("Test error message", error_code="TEST-001")
    time.sleep(3)
    
    print("\nTest complete! Returning to idle...")
    display.change_state('idle')
    
    print("\nServer will continue running.")
    print("View at: http://localhost:5000")
    print("Press Ctrl+C to stop, or wait 10s to replay...")
    
    try:
        countdown = 10
        while countdown > 0:
            print(f"Replaying in {countdown}s...", end='\r')
            time.sleep(1)
            countdown -= 1
        print("\nReplaying demo...")
        main()  # Replay the demo
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()
