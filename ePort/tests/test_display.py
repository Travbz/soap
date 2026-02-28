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
import random
from datetime import datetime, timezone, timedelta
from ePort.src.display_server import DisplayServer
from ePort.src.product_manager import ProductManager
from ePort.config import (
    PRODUCTS_CONFIG_PATH,
    SALES_TAX_RATE,
    RECEIPT_TIMEZONE_OFFSET,
    RECEIPT_TIMEZONE_NAME
)

try:
    import tty
    import termios
    import select
    HAS_TTY = True
except ImportError:
    HAS_TTY = False

# Global display server instance
display = None

def is_out_of_order(product):
    """Return True if a product is marked out of order."""
    status_ooo = str(product.get('status', '')).strip().upper() == 'OOO'
    has_message = bool(str(product.get('message', '')).strip())
    return status_ooo or has_message

def load_products_for_test():
    """Load products from real config to avoid hardcoded test data."""
    manager = ProductManager(PRODUCTS_CONFIG_PATH)
    return [
        {
            'id': p.id,
            'name': p.name,
            'unit': p.unit,
            'price_per_unit': p.price_per_unit,
            'status': p.status,
            'message': p.message
        }
        for p in manager.list_products()
    ]

def build_receipt_totals(subtotal):
    """Build subtotal/tax/total/timestamp values for receipt payload."""
    tax = round(subtotal * SALES_TAX_RATE, 2)
    total = round(subtotal + tax, 2)
    tz = timezone(timedelta(hours=RECEIPT_TIMEZONE_OFFSET))
    timestamp = datetime.now(tz).strftime('%m/%d/%Y %I:%M %p') + ' ' + RECEIPT_TIMEZONE_NAME
    return subtotal, tax, total, timestamp

def run_demo():
    """Run demo sequence"""
    products = list(display.products)
    available_products = [p for p in products if not is_out_of_order(p)]
    ooo_products = [p for p in products if is_out_of_order(p)]

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

    running_total = 0.0
    dispensed_totals = {}

    # Simulate dispensing on available products loaded from real config
    for index, product in enumerate(available_products[:2]):
        final_qty = round(random.uniform(2.0, 14.0), 1)
        print("   Dispensing {}... target {}{}".format(
            product['name'],
            final_qty,
            product['unit']
        ))
        step_ounces = round(final_qty / 4.0, 2)
        qty = 0.0
        price = 0.0
        for i in range(1, 5):
            if i < 4:
                qty = round(i * step_ounces, 1)
            else:
                qty = final_qty
            price = round(qty * product['price_per_unit'], 2)
            display.update_product(
                product_id=product['id'],
                product_name=product['name'],
                quantity=qty,
                unit=product['unit'],
                price=price,
                is_active=True
            )
            display.update_total(running_total + price)
            time.sleep(0.5)

        running_total = round(running_total + price, 2)
        dispensed_totals[product['id']] = {
            'product_name': product['name'],
            'quantity': qty,
            'unit': product['unit'],
            'price': price
        }
        display.update_product(
            product_id=product['id'],
            product_name=product['name'],
            quantity=qty,
            unit=product['unit'],
            price=price,
            is_active=False
        )

    # Attempt updates on OOO products; should not crash test flow
    for ooo_product in ooo_products:
        print("   {} is OOO - attempting update (should not crash)...".format(ooo_product['name']))
        try:
            display.update_product(
                product_id=ooo_product['id'],
                product_name=ooo_product['name'],
                quantity=1.0,
                unit=ooo_product['unit'],
                price=round(ooo_product['price_per_unit'], 2),
                is_active=True
            )
            display.update_total(running_total)
        except Exception as e:
            print("   OOO update failed safely: {}".format(e))
    
    time.sleep(1)
    
    print("5. Waiting - press done button")
    display.change_state('waiting')
    time.sleep(3)
    
    print("6. Complete - showing receipt")
    receipt_items = list(dispensed_totals.values())
    subtotal = round(sum(item['price'] for item in receipt_items), 2)
    subtotal, tax, receipt_total, timestamp = build_receipt_totals(subtotal)
    display.show_receipt(
        items=receipt_items,
        subtotal=subtotal,
        tax=tax,
        total=receipt_total,
        timestamp=timestamp
    )
    time.sleep(5)
    
    print("7. Declined card")
    display.change_state('declined')
    time.sleep(3)
    
    print("8. Error state")
    display.show_error("We're sorry for the inconvenience", error_code="TEST-001")
    time.sleep(3)
    
    print("\nDemo complete! Returning to idle...")
    
    # Reset all products to zero
    for product in products:
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
    
    products = list(display.products)
    
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
                subtotal = round(sum(item['price'] for item in items), 2)
                subtotal, tax, total, timestamp = build_receipt_totals(subtotal)
                display.show_receipt(
                    items=items,
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    timestamp=timestamp
                )
        elif state == 'error':
            display.show_error("We're sorry for the inconvenience", error_code="TEST-001")
    
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
    once_mode = '--once' in sys.argv
    
    print("=" * 60)
    print("DISPLAY SERVER TEST")
    print("=" * 60)
    
    # Load product data from real config
    products = load_products_for_test()
    
    # Initialize and start server
    display = DisplayServer(host='localhost', port=5000, products=products)
    display.start(background=True)
    
    print(f"\nDisplay server running on http://localhost:5000")
    print("Open in browser\n")
    
    display.change_state('idle')
    time.sleep(1)
    
    if once_mode:
        print("ONCE MODE - Running one demo cycle")
        run_demo()
        print("Shutting down...")
        sys.exit(0)
    elif loop_mode:
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
