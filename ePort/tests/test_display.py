"""
Test script for display server

Run this to test the display without the full vending machine system.

Usage:
  python3 -m ePort.tests.test_display          (default: manual mode with arrow keys)
  python3 -m ePort.tests.test_display --loop   (auto-loop through all states)

Manual mode: Use LEFT/RIGHT arrow keys to navigate between states
"""

import time
import sys
from ePort.src.display_server import DisplayServer

try:
    import tty
    import termios
    import select
    HAS_TTY = True
except ImportError:
    HAS_TTY = False

# Global display server instance
display = None

def run_demo():
    """Run demo sequence"""
    print("1. Idle state (swipe card)")
    display.change_state('idle')
    time.sleep(2)
    
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
    
    print("\nDemo complete! Returning to idle...")
    
    # Reset all products to zero
    for product in [
        {'id': 'soap_hand', 'name': 'HAND SOAP', 'unit': 'oz'},
        {'id': 'soap_dish', 'name': 'DISH SOAP', 'unit': 'oz'},
        {'id': 'soap_laundry', 'name': 'LAUNDRY GEL', 'unit': 'oz'}
    ]:
        display.update_product(
            product_id=product['id'],
            product_name=product['name'],
            quantity=0,
            unit=product['unit'],
            price=0,
            is_active=False
        )
    
    display.update_total(0)
    display.change_state('idle')

def manual_mode():
    """Manual navigation mode with arrow keys"""
    global display
    
    states = ['idle', 'authorizing', 'ready', 'dispensing', 'waiting', 'complete', 'declined', 'error']
    state_names = ['Idle', 'Authorizing', 'Ready', 'Dispensing', 'Waiting', 'Complete', 'Declined', 'Error']
    current_index = 0
    
    products = [
        {'id': 'soap_hand', 'name': 'HAND SOAP', 'unit': 'oz', 'price_per_unit': 0.15},
        {'id': 'soap_dish', 'name': 'DISH SOAP', 'unit': 'oz', 'price_per_unit': 0.12},
        {'id': 'soap_laundry', 'name': 'LAUNDRY GEL', 'unit': 'oz', 'price_per_unit': 0.10}
    ]
    
    def show_state(index):
        state = states[index]
        print(f"\r[{index + 1}/8] {state_names[index]:15} (← prev | next → | q=quit)  ", end='', flush=True)
        display.change_state(state)
        
        # Add mock data for dispensing/waiting/complete states
        if state in ['dispensing', 'waiting', 'complete']:
            for i, product in enumerate(products):
                qty = (i + 1) * 4.2
                price = qty * product['price_per_unit']
                display.update_product(
                    product_id=product['id'],
                    product_name=product['name'],
                    quantity=qty,
                    unit=product['unit'],
                    price=price,
                    is_active=(i == 0 and state == 'dispensing')
                )
            display.update_total(sum((i + 1) * 4.2 * p['price_per_unit'] for i, p in enumerate(products)))
            
            if state == 'complete':
                items = [
                    {'product_name': p['name'], 'quantity': (i + 1) * 4.2, 
                     'unit': p['unit'], 'price': (i + 1) * 4.2 * p['price_per_unit']}
                    for i, p in enumerate(products)
                ]
                total = sum(item['price'] for item in items)
                display.show_receipt(items=items, total=total)
        elif state == 'error':
            display.show_error("Test error message", error_code="TEST-001")
    
    show_state(current_index)
    
    if not HAS_TTY:
        print("\n\nWarning: Arrow key navigation not available on this system")
        print("Press Ctrl+C to quit")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return
    
    fd = sys.stdin.fileno()
    try:
        old_settings = termios.tcgetattr(fd)
    except termios.error:
        print("\n\nWarning: Terminal doesn't support interactive mode")
        print("Press Ctrl+C to quit")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return
    
    try:
        tty.setcbreak(fd)
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                
                if ch == '\x1b':  # Escape sequence
                    ch = sys.stdin.read(2)
                    if ch == '[C':  # Right arrow
                        current_index = (current_index + 1) % len(states)
                        show_state(current_index)
                    elif ch == '[D':  # Left arrow
                        current_index = (current_index - 1) % len(states)
                        show_state(current_index)
                elif ch.lower() == 'q':
                    break
                    
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\n")


def main():
    """Main entry point"""
    global display
    
    # Check for command line argument
    loop_mode = '--loop' in sys.argv
    
    print("=" * 60)
    print("DISPLAY SERVER TEST")
    print("=" * 60)
    
    # Mock product data
    products = [
        {'id': 'soap_hand', 'name': 'HAND SOAP', 'unit': 'oz', 'price_per_unit': 0.15},
        {'id': 'soap_dish', 'name': 'DISH SOAP', 'unit': 'oz', 'price_per_unit': 0.12},
        {'id': 'soap_laundry', 'name': 'LAUNDRY GEL', 'unit': 'oz', 'price_per_unit': 0.10}
    ]
    
    # Initialize and start server
    display = DisplayServer(host='localhost', port=5000, products=products)
    display.start(background=True)
    
    print(f"\nDisplay server running on http://localhost:5000")
    print("Open in browser\n")
    
    display.change_state('idle')
    time.sleep(1)
    
    if loop_mode:
        print("LOOP MODE - Continuously cycling through states")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                run_demo()
                print("\nLooping again in 3 seconds...")
                time.sleep(3)
        except KeyboardInterrupt:
            print("\nShutting down...")
            sys.exit(0)
    else:
        print("MANUAL MODE - Use arrow keys to navigate")
        print("Press LEFT/RIGHT arrows to switch states, Q to quit\n")
        manual_mode()
        print("Shutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()
