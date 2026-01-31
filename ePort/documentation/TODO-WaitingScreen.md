# Waiting Screen Implementation TODO

## Overview
The "waiting" screen (PRESS DONE BUTTON) should automatically display after 10 seconds of button inactivity during an active transaction.

## Configuration
✅ Added `WAITING_SCREEN_TIMEOUT = 10` to `/Users/travops/soap/ePort/config/__init__.py`

## Frontend (Display)
✅ HTML template created (`waiting-screen` state)
✅ CSS styling complete
✅ JavaScript handles state transitions
✅ Product bar MFE shows purchased products

## Backend Implementation Needed

### Location: `/Users/travops/soap/ePort/main.py`

In the `dispense_products()` function, add logic to:

1. **Track last button press time**
   ```python
   from ..config import WAITING_SCREEN_TIMEOUT
   last_button_press_time = time.time()
   ```

2. **In the dispensing loop, check for inactivity**
   ```python
   # Inside the main dispensing loop
   current_time = time.time()
   time_since_last_press = current_time - last_button_press_time
   
   # Show waiting screen if inactive for WAITING_SCREEN_TIMEOUT seconds
   if time_since_last_press >= WAITING_SCREEN_TIMEOUT:
       if display and display.current_state != 'waiting':
           display.change_state('waiting')
   else:
       if display and display.current_state != 'dispensing':
           display.change_state('dispensing')
   ```

3. **Update last_button_press_time when any button is pressed**
   ```python
   # When product button pressed
   if GPIO.input(button_pin) == GPIO.LOW:
       last_button_press_time = time.time()
       if display:
           display.change_state('dispensing')
   ```

4. **Reset when switching products**
   ```python
   def on_product_switch(old_product, new_product):
       nonlocal last_button_press_time
       last_button_press_time = time.time()
       # ... rest of product switch logic
   ```

## Testing
Update test_display.py to include waiting state in the demo loop between dispensing and complete.

## Notes
- Waiting screen shows when: `time_since_last_button_press >= WAITING_SCREEN_TIMEOUT`
- Returns to dispensing when: any product button is pressed
- Transaction completes when: DONE button is pressed OR `DISPENSING_INACTIVITY_TIMEOUT` reached
