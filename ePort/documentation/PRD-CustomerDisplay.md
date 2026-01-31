# Product Requirements Document: Customer Guidance Display System

**Version:** 2.0  
**Status:** In Development  
**Date:** January 2026  
**Updated:** January 27, 2026  
**Related:** PRD-MultiProduct.md

---

## Executive Summary

Add visual guidance system to display real-time transaction information, product counters, and instructions to customers throughout the transaction flow. Based on artist concept designs and actual customer journey analysis.

---

## Problem Statement

**Current:** Text-only terminal output with timestamps and log levels. Customers see debug messages, unclear instructions, and no real-time feedback during dispensing.

**Desired:** Clean visual interface showing live product counters, transaction totals, warnings, and clear instructions at each step. No technical logs visible to customers.

---

## Goals & Non-Goals

### Goals
- ✅ Real-time product counters (quantity and price per product)
- ✅ Live transaction total updates during dispensing
- ✅ Clear visual warnings (overfill prevention, stop early)
- ✅ Product selection guidance (which button is which)
- ✅ Itemized receipt display after transaction
- ✅ Customer-friendly interface (no logs, timestamps, or debug info)
- ✅ State-driven display matching actual customer journey

### Non-Goals
- ❌ Touchscreen interaction (physical buttons only)
- ❌ Audio playback (silent operation)
- ❌ Video animations (static graphics and HTML/CSS animations only)
- ❌ Complex multimedia (keep it lightweight for Raspberry Pi)

---

## User Stories

### US-1: Customer Knows When to Swipe Card
**As a** customer  
**I want to** see clear instructions to swipe my card when the machine is idle  
**So that** I know how to start a transaction

**Acceptance:** Display shows "SWIPE CARD TO BEGIN" with card graphic when idle

---

### US-2: Customer Sees Live Product Counters
**As a** customer  
**I want to** see real-time quantity and price for each product I'm dispensing  
**So that** I know exactly how much I've taken and what it costs

**Acceptance:** Display updates in real-time showing "Hand Soap: 7.2oz $1.08" as I dispense

---

### US-3: Customer Receives Overfill Warning
**As a** customer  
**I want to** see a clear warning about overfilling my container  
**So that** I stop before it overflows

**Acceptance:** Display shows "PAY ATTENTION - STOP EARLY!" with container visual and red line

---

### US-4: Customer Knows Which Button is Which Product
**As a** customer  
**I want to** see which physical button corresponds to which product  
**So that** I don't accidentally dispense the wrong product

**Acceptance:** Display shows button layout diagram after card authorization

---

### US-5: Customer Sees Running Transaction Total
**As a** customer  
**I want to** see my total cost update as I dispense multiple products  
**So that** I can stay within my budget

**Acceptance:** Display shows "TOTAL: $2.12" that updates live during dispensing

---

### US-6: Customer Receives Itemized Receipt
**As a** customer  
**I want to** see a detailed receipt after pressing DONE  
**So that** I know exactly what I paid for

**Acceptance:** Display shows "THANKS FOR REFILLING!" with itemized list and total

---

### US-7: Owner Updates Display Styling
**As a** company owner  
**I want to** update colors, fonts, and layout via HTML/CSS  
**So that** I can match store branding without coding

**Acceptance:** Owner can edit CSS file, changes apply on browser refresh

---

## Technical Design

### Architecture Decision: Web-Based Display

**Decision:** Use Chromium browser in kiosk mode with Flask backend

**Rationale:**
- Artist's sketch maps directly to HTML/CSS layout (tables, text, containers)
- Real-time updates via WebSocket (live product counters)
- Owner can modify styling without Python knowledge
- Proven on Raspberry Pi 4
- Rapid prototyping and iteration
- Responsive design handles different monitor sizes

**Alternatives Considered:**
- pygame: Complex layout implementation, harder to style
- Qt/QML: Heavy dependency, steeper learning curve
- Native Python GUI: Poor performance for real-time updates

### System Architecture

```
┌─────────────────────────────────────────┐
│          main.py                        │
│      (Transaction Logic)                │
│  - Payment processing                   │
│  - Product dispensing                   │
│  - Transaction tracking                 │
└──────────┬──────────────────────────────┘
           │ HTTP POST / WebSocket
           ▼
┌─────────────────────────────────────────┐
│      Flask Display Server               │
│   (src/display_server.py)               │
├─────────────────────────────────────────┤
│ REST API Endpoints:                     │
│ - POST /api/state (change state)        │
│ - POST /api/update (product counter)    │
│ - POST /api/receipt (show receipt)      │
│                                         │
│ WebSocket Events:                       │
│ - emit('update_product', data)          │
│ - emit('show_receipt', data)            │
│ - emit('change_state', state)           │
└──────────┬──────────────────────────────┘
           │ Serves HTML/CSS/JS
           ▼
┌─────────────────────────────────────────┐
│  Chromium Browser (Kiosk Mode)          │
│  http://localhost:5000                  │
├─────────────────────────────────────────┤
│ - Fullscreen display                    │
│ - Auto-start on boot                    │
│ - No browser UI elements                │
│ - Real-time WebSocket connection        │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      HTML/CSS/JavaScript                │
│  (display/templates/)                   │
├─────────────────────────────────────────┤
│ - index.html (layout)                   │
│ - styles.css (branding)                 │
│ - app.js (real-time updates)            │
└─────────────────────────────────────────┘
```

---

## Customer Journey & Display States

### Complete State Flow (7 States)

```
┌──────────────────────────────────────────────────────────┐
│  STATE 1: idle                                           │
│  TRIGGER: Machine ready, no transaction                  │
│  CODE: Waiting for ePort status                          │
├──────────────────────────────────────────────────────────┤
│  DISPLAY:                                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │         [CARD GRAPHIC with swipe animation]       │  │
│  │                                                    │  │
│  │              SWIPE OR TAP CARD                     │  │
│  │                 TO BEGIN                           │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────┘
                       │ Customer swipes card
                       ▼
┌──────────────────────────────────────────────────────────┐
│  STATE 2: authorizing                                    │
│  TRIGGER: Card swiped, requesting authorization          │
│  CODE: safe_authorization_request(payment)               │
├──────────────────────────────────────────────────────────┤
│  DISPLAY:                                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │         [PROCESSING SPINNER animation]            │  │
│  │                                                    │  │
│  │           AUTHORIZING PAYMENT...                   │  │
│  │              Please wait                           │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────┬───────────────────┬───────────────────────────┘
           │ Approved          │ Declined
           ▼                   ▼
┌──────────────────────┐    ┌─────────────────────────────┐
│  STATE 3: ready      │    │  STATE 4: declined          │
│  (Product Selection) │    │  TRIGGER: Card declined     │
│  TRIGGER: Auth OK    │    │  CODE: status.startswith    │
│  CODE: status == b'9'│    │        (b'3')               │
├──────────────────────┤    ├─────────────────────────────┤
│  DISPLAY:            │    │  DISPLAY:                   │
│  ┌────────────────┐  │    │  ┌───────────────────────┐  │
│  │ AUTHORIZED ✓   │  │    │  │        [X ICON]       │  │
│  │                │  │    │  │                       │  │
│  │ [Button Layout]│  │    │  │   CARD DECLINED       │  │
│  │  Left: Hand    │  │    │  │  Please try another   │  │
│  │  Mid: Dish     │  │    │  │       card            │  │
│  │  Right: Laundry│  │    │  └───────────────────────┘  │
│  │                │  │    │  (Show 5s, return to idle)  │
│  │ HOLD BUTTON TO │  │    └─────────────────────────────┘
│  │ DISPENSE       │  │
│  │ Press DONE when│  │
│  │ finished       │  │
│  └────────────────┘  │
└──────┬───────────────┘
       │ Customer presses product button
       ▼
┌───────────────────────────────────────────────────────────┐
│  STATE 5: dispensing (ARTIST'S PRIMARY SCREEN)            │
│  TRIGGER: Product button pressed                          │
│  CODE: handle_dispensing(), on_flowmeter_pulse()          │
├───────────────────────────────────────────────────────────┤
│  DISPLAY (Based on Artist's Sketch):                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ⚠️  PAY ATTENTION - STOP EARLY!                     │  │
│  │                                                     │  │
│  │  [Container Visual]      Currently Dispensing:     │  │
│  │  ┌──────────────┐        ► HAND SOAP ◄             │  │
│  │  │              │        (Hold button)              │  │
│  │  │   ▓▓▓▓▓▓▓    │                                   │  │
│  │  │──RED LINE────│      Products This Transaction:  │  │
│  │  │              │      ┌────────┬──────┬─────────┐ │  │
│  │  │              │      │ HAND   │ DISH │ LAUNDRY │ │  │
│  │  └──────────────┘      ├────────┼──────┼─────────┤ │  │
│  │  DON'T OVERFILL       │ 7.2oz  │ 8.7oz│  0oz    │ │  │
│  │                        │ $1.08  │ $1.04│  $0.00  │ │  │
│  │                        └────────┴──────┴─────────┘ │  │
│  │                                                     │  │
│  │                        TOTAL: $2.12                 │  │
│  │                                                     │  │
│  │  [DONE BUTTON GRAPHIC]                              │  │
│  │  Press DONE or pick another product to continue    │  │
│  │                                                     │  │
│  │  ⏱️ Time remaining: 4:23                            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  REAL-TIME UPDATES:                                       │
│  - Product counters update on each flowmeter pulse       │
│  - Total recalculates instantly                           │
│  - Current product highlights when button pressed         │
│  - Timer counts down from 5:00 (max session)             │
│  - Warning shows at 45s inactivity                        │
└──────────┬────────────────────────────────────────────────┘
           │ Customer presses DONE button
           ▼
┌───────────────────────────────────────────────────────────┐
│  STATE 6: complete (ARTIST'S RECEIPT SCREEN)              │
│  TRIGGER: Done button pressed, transaction sent           │
│  CODE: on_done_button(), transaction.get_summary()        │
├───────────────────────────────────────────────────────────┤
│  DISPLAY (Based on Artist's Sketch):                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                                                     │  │
│  │           THANKS FOR REFILLING!                     │  │
│  │                                                     │  │
│  │           Your Receipt:                             │  │
│  │  ┌───────────────────────────────────────────────┐ │  │
│  │  │                                               │ │  │
│  │  │  HANDSOAP    19kg                             │ │  │
│  │  │  3.2oz .................... $7.50            │ │  │
│  │  │                                               │ │  │
│  │  │  DISH SOAP   13kg                             │ │  │
│  │  │  7.9oz .................... $8.03            │ │  │
│  │  │                                               │ │  │
│  │  │  LAUNDRY     10kg                             │ │  │
│  │  │  10.8oz ...................  $1.28           │ │  │
│  │  │                                               │ │  │
│  │  │  ─────────────────────────────────────        │ │  │
│  │  │  TOTAL ........................ $11.03        │ │  │
│  │  │                                               │ │  │
│  │  └───────────────────────────────────────────────┘ │  │
│  │                                                     │  │
│  │           Returning to home in 8...                 │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  BEHAVIOR:                                                │
│  - Display for 10 seconds                                 │
│  - Show countdown timer                                   │
│  - Auto-return to idle state                              │
└──────────┬────────────────────────────────────────────────┘
           │ Timeout (10s)
           ▼
      (Return to STATE 1: idle)


┌───────────────────────────────────────────────────────────┐
│  STATE 7: error (Exception Handling)                      │
│  TRIGGER: Payment error, hardware failure, timeout        │
│  CODE: except MachineHardwareError, PaymentProtocolError  │
├───────────────────────────────────────────────────────────┤
│  DISPLAY:                                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                                                     │  │
│  │              [ERROR ICON]                           │  │
│  │                                                     │  │
│  │          MACHINE ERROR                              │  │
│  │                                                     │  │
│  │     Please contact staff for assistance             │  │
│  │                                                     │  │
│  │     Error code: [error details]                     │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  BEHAVIOR:                                                │
│  - Display for 10 seconds or until reset                  │
│  - Log full error details                                 │
│  - Attempt machine reset                                  │
│  - Return to idle if recoverable                          │
└───────────────────────────────────────────────────────────┘
```

---

## Flask Display Server

**Location:** `ePort/src/display_server.py`

### Server Class Design

```python
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from typing import List, Dict
import threading

class DisplayServer:
    """
    Web-based display server using Flask and WebSocket
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5000):
        """
        Initialize Flask server with WebSocket support
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.app = Flask(__name__, 
                        template_folder='../display/templates',
                        static_folder='../display/static')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port
        self.current_state = "idle"
        self._setup_routes()
    
    def start(self, background: bool = True) -> None:
        """
        Start the Flask server
        
        Args:
            background: If True, run in background thread
        """
        if background:
            thread = threading.Thread(
                target=lambda: self.socketio.run(
                    self.app, 
                    host=self.host, 
                    port=self.port,
                    debug=False
                )
            )
            thread.daemon = True
            thread.start()
        else:
            self.socketio.run(self.app, host=self.host, port=self.port)
    
    def change_state(self, state: str) -> None:
        """
        Change display state
        
        Args:
            state: State name (idle, authorizing, ready, dispensing, complete, error)
        """
        self.current_state = state
        self.socketio.emit('change_state', {'state': state})
    
    def update_product(self, product_id: str, product_name: str, 
                      quantity: float, unit: str, price: float,
                      is_active: bool = False) -> None:
        """
        Update product counter in real-time
        
        Args:
            product_id: Product identifier (soap_hand, soap_dish, etc.)
            product_name: Display name
            quantity: Current quantity dispensed
            unit: Unit of measurement (oz, ml)
            price: Current price for this product
            is_active: Whether this product is currently being dispensed
        """
        self.socketio.emit('update_product', {
            'product_id': product_id,
            'product_name': product_name,
            'quantity': quantity,
            'unit': unit,
            'price': price,
            'is_active': is_active
        })
    
    def update_total(self, total: float) -> None:
        """
        Update transaction total
        
        Args:
            total: Current transaction total in dollars
        """
        self.socketio.emit('update_total', {'total': total})
    
    def show_receipt(self, items: List[Dict], total: float) -> None:
        """
        Show final receipt
        
        Args:
            items: List of items with {product_name, quantity, unit, price}
            total: Final transaction total
        """
        self.change_state('complete')
        self.socketio.emit('show_receipt', {
            'items': items,
            'total': total
        })
    
    def show_error(self, error_message: str, error_code: str = None) -> None:
        """
        Show error screen
        
        Args:
            error_message: User-friendly error message
            error_code: Optional error code for staff
        """
        self.change_state('error')
        self.socketio.emit('show_error', {
            'message': error_message,
            'code': error_code
        })
    
    def update_timer(self, seconds_remaining: int, warning: bool = False) -> None:
        """
        Update inactivity/session timer
        
        Args:
            seconds_remaining: Seconds until timeout
            warning: If True, show warning styling
        """
        self.socketio.emit('update_timer', {
            'seconds': seconds_remaining,
            'warning': warning
        })
```

---

## Configuration

### Display Configuration (config/__init__.py)

```python
# Display server settings
DISPLAY_ENABLED = True  # Set to False to disable display (testing mode)
DISPLAY_HOST = 'localhost'
DISPLAY_PORT = 5000
DISPLAY_AUTO_START = True  # Auto-start server with main.py

# Display timeouts
RECEIPT_DISPLAY_TIMEOUT = 10  # Seconds to show receipt before returning to idle
ERROR_DISPLAY_TIMEOUT = 10    # Seconds to show error before reset attempt

# Display styling (can be overridden in CSS)
DISPLAY_WARNING_COLOR = '#FF0000'  # Red for warnings
DISPLAY_SUCCESS_COLOR = '#00FF00'  # Green for success
DISPLAY_BACKGROUND = '#000000'     # Black background
DISPLAY_TEXT_COLOR = '#FFFFFF'     # White text
```

### CSS Styling (display/static/styles.css)

Owner can customize colors, fonts, sizing without touching Python:

```css
/* Main layout */
body {
    background: #000000;
    color: #FFFFFF;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

/* Warning section */
.warning {
    color: #FF0000;
    font-size: 48px;
    font-weight: bold;
    text-align: center;
    padding: 20px;
}

/* Container visual */
.container-visual {
    width: 400px;
    height: 600px;
    border: 3px solid #FFFFFF;
    position: relative;
    margin: 20px auto;
}

.red-line {
    position: absolute;
    top: 20%;
    width: 100%;
    border-top: 4px solid #FF0000;
}

/* Product counters table */
.product-counters {
    font-size: 36px;
    margin: 40px auto;
    width: 90%;
}

.product-counters table {
    width: 100%;
    border-collapse: collapse;
}

.product-counters td {
    padding: 15px;
    border: 1px solid #FFFFFF;
}

.active-product {
    background-color: #333333;
    font-weight: bold;
}

/* Receipt styling */
.receipt {
    background: #FFFFFF;
    color: #000000;
    padding: 40px;
    margin: 40px auto;
    width: 80%;
    max-width: 800px;
    font-family: 'Courier New', monospace;
}

/* Timer warning */
.timer-warning {
    color: #FFAA00;
    font-size: 32px;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.5; }
}
```

---

## Technology Stack (DECISION RECORD)

### Selected: Web-Based Display with Chromium Kiosk Mode

**Final Decision:** Flask backend + HTML/CSS/JavaScript frontend + Chromium browser

**Key Reasons:**
1. **Artist's layout maps perfectly to HTML/CSS** - Tables, text positioning, container visuals
2. **Real-time updates trivial with WebSocket** - Product counters update instantly
3. **Owner can modify styling** - Edit CSS without Python knowledge
4. **Rapid iteration** - Build and test UI in browser dev tools
5. **Proven on Raspberry Pi** - Chromium runs well on RPi 4
6. **No custom rendering engine** - Browser handles everything

### Technology Components

**Backend:**
- Flask 2.0+ (web server)
- Flask-SocketIO (WebSocket support for real-time updates)
- Python 3.7+ (existing requirement)

**Frontend:**
- HTML5 (structure)
- CSS3 (styling, animations)
- JavaScript (real-time updates via WebSocket)
- Socket.IO client library

**Display:**
- Chromium browser in kiosk mode
- Auto-start on boot
- Fullscreen, no UI elements
- URL: `http://localhost:5000`

### Alternatives Considered & Rejected

**pygame:**
- ❌ Complex custom layout engine needed
- ❌ Manual text positioning and sizing
- ❌ Harder to match artist's vision precisely
- ❌ Owner cannot easily update styling

**PyQt5/QML:**
- ❌ Heavy dependency (200MB+)
- ❌ Steeper learning curve
- ❌ Overkill for this use case

**Native Python GUI (Tkinter):**
- ❌ Poor performance for real-time updates
- ❌ Limited styling capabilities
- ❌ Outdated appearance

---

## File Structure

```
ePort/
├── src/
│   ├── display_server.py           # Flask server (NEW)
│   ├── payment.py                  # Existing
│   ├── machine.py                  # Existing
│   └── ...
├── display/                        # NEW DIRECTORY
│   ├── templates/
│   │   ├── index.html              # Main display layout
│   │   ├── idle.html               # Swipe card screen
│   │   ├── authorizing.html        # Processing screen
│   │   ├── ready.html              # Product selection screen
│   │   ├── dispensing.html         # Live counter screen (artist's main)
│   │   ├── complete.html           # Receipt screen (artist's receipt)
│   │   └── error.html              # Error screen
│   └── static/
│       ├── styles.css              # Main stylesheet
│       ├── app.js                  # WebSocket client & updates
│       └── images/
│           ├── card_graphic.svg    # Card swipe visual
│           ├── spinner.gif         # Loading animation
│           ├── container.svg       # Container with red line
│           ├── button_layout.svg   # Button diagram
│           └── logo.png            # Store branding (optional)
├── config/
│   └── __init__.py                 # Add DISPLAY_* constants
└── main.py                         # Integration point
```

### Key Files

**display/templates/dispensing.html** - Artist's primary screen:
```html
<div class="dispensing-screen">
    <div class="warning">⚠️ PAY ATTENTION - STOP EARLY!</div>
    
    <div class="main-content">
        <div class="container-visual">
            <div class="red-line"></div>
            <div class="fill-level" id="fill-level"></div>
            <p>DON'T OVERFILL</p>
        </div>
        
        <div class="product-info">
            <p class="currently-dispensing">
                Currently Dispensing: <span id="current-product">--</span>
            </p>
            
            <table class="product-counters">
                <tr>
                    <th>HAND</th>
                    <th>DISH</th>
                    <th>LAUNDRY</th>
                    <th>TOTAL</th>
                </tr>
                <tr>
                    <td id="hand-qty">0oz</td>
                    <td id="dish-qty">0oz</td>
                    <td id="laundry-qty">0oz</td>
                    <td id="total-qty">0oz</td>
                </tr>
                <tr>
                    <td id="hand-price">$0.00</td>
                    <td id="dish-price">$0.00</td>
                    <td id="laundry-price">$0.00</td>
                    <td id="total-price">$0.00</td>
                </tr>
            </table>
        </div>
    </div>
    
    <div class="instructions">
        <img src="/static/images/done_button.svg" alt="Done Button">
        <p>Press DONE or pick another product to continue</p>
    </div>
    
    <div class="timer" id="session-timer">Time remaining: 5:00</div>
</div>
```

**display/templates/complete.html** - Artist's receipt screen:
```html
<div class="receipt-screen">
    <h1>THANKS FOR REFILLING!</h1>
    
    <div class="receipt">
        <p class="receipt-header">Your Receipt:</p>
        <div id="receipt-items">
            <!-- Populated by JavaScript -->
        </div>
        <div class="receipt-total">
            TOTAL ................ $<span id="receipt-total">0.00</span>
        </div>
    </div>
    
    <p class="countdown">Returning to home in <span id="countdown">10</span>...</p>
</div>
```

---

## Integration with main.py

### Main Entry Point Modifications

```python
# main.py - Add display server integration

from .src.display_server import DisplayServer
from .config import DISPLAY_ENABLED, DISPLAY_HOST, DISPLAY_PORT

def main():
    """Main entry point with display integration"""
    
    # ... existing GPIO and serial setup ...
    
    # Initialize display server (if enabled)
    display = None
    if DISPLAY_ENABLED:
        try:
            display = DisplayServer(host=DISPLAY_HOST, port=DISPLAY_PORT)
            display.start(background=True)
            logger.info("Display server started on http://{}:{}".format(
                DISPLAY_HOST, DISPLAY_PORT
            ))
            time.sleep(1)  # Give server time to start
        except Exception as e:
            logger.error(f"Failed to start display server: {e}")
            logger.warning("Continuing without display...")
            display = None
    
    # Main loop
    while True:
        try:
            # STATE 1: Idle - waiting for card
            if display:
                display.change_state("idle")
            
            status = safe_status_check(payment)
            
            if status == b'6':  # Disabled - ready for card
                # Customer swipes card
                # STATE 2: Authorizing
                if display:
                    display.change_state("authorizing")
                
                safe_authorization_request(payment, AUTH_AMOUNT_CENTS)
                time.sleep(AUTHORIZATION_STATUS_CHECK_DELAY)
                
                auth_status = safe_status_check(payment)
                
                if auth_status == b'9':  # Approved
                    # STATE 3: Ready - show product selection
                    if display:
                        display.change_state("ready")
                    
                elif auth_status.startswith(b'3'):  # Declined
                    # STATE 4: Declined
                    if display:
                        display.change_state("declined")
                    time.sleep(5)
                    continue
            
            elif status == b'9':  # Authorized - ready to dispense
                # STATE 5: Dispensing (artist's main screen)
                if display:
                    display.change_state("dispensing")
                
                try:
                    handle_dispensing(machine, payment, product_manager, 
                                    transaction_tracker, display)
                except Exception as e:
                    # STATE 7: Error
                    if display:
                        display.show_error(
                            "Machine error. Please contact staff.",
                            error_code=str(e)
                        )
                    logger.error(f"Dispensing error: {e}")
                    time.sleep(ERROR_DISPLAY_TIMEOUT)
            
            time.sleep(STATUS_POLL_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            if display:
                display.show_error("System error", error_code=str(e))
            time.sleep(5)


def handle_dispensing(machine, payment, product_manager, transaction, display):
    """
    Handle multi-product dispensing with real-time display updates
    
    Args:
        machine: MachineController instance
        payment: EPortProtocol instance
        product_manager: ProductManager instance
        transaction: TransactionTracker instance
        display: DisplayServer instance (or None)
    """
    
    current_product_ounces = 0.0
    current_product = None
    session_start_time = time.time()
    last_activity_time = time.time()
    
    def on_flowmeter_pulse(channel):
        """Called on each flowmeter pulse - update display in real-time"""
        nonlocal current_product_ounces, last_activity_time
        
        if current_product:
            # Calculate current quantity
            pulses = machine.pulse_count
            current_product_ounces = pulses / current_product.pulses_per_unit
            price = current_product.calculate_price(current_product_ounces)
            
            # Update display with live counter
            if display:
                display.update_product(
                    product_id=current_product.id,
                    product_name=current_product.name,
                    quantity=current_product_ounces,
                    unit=current_product.unit,
                    price=price,
                    is_active=True
                )
                
                # Update total
                total = transaction.get_total() + price
                display.update_total(total)
            
            last_activity_time = time.time()
    
    def on_product_switch(product):
        """Called when customer switches products"""
        nonlocal current_product_ounces
        
        prev_product = machine.get_current_product()
        if prev_product and current_product_ounces > 0:
            price = prev_product.calculate_price(current_product_ounces)
            transaction.add_item(
                product_id=prev_product.id,
                product_name=prev_product.name,
                quantity=current_product_ounces,
                unit=prev_product.unit,
                price=price
            )
            
            # Update display to show recorded product
            if display:
                display.update_product(
                    product_id=prev_product.id,
                    product_name=prev_product.name,
                    quantity=current_product_ounces,
                    unit=prev_product.unit,
                    price=price,
                    is_active=False
                )
        
        current_product_ounces = 0.0
        logger.info(f"Switching to: {product.name}")
    
    def on_done_button():
        """Called when customer presses done - show receipt"""
        nonlocal current_product_ounces
        
        # Record final product
        current_product = machine.get_current_product()
        if current_product and current_product_ounces > 0:
            price = current_product.calculate_price(current_product_ounces)
            transaction.add_item(
                product_id=current_product.id,
                product_name=current_product.name,
                quantity=current_product_ounces,
                unit=current_product.unit,
                price=price
            )
        
        # STATE 6: Complete - show receipt (artist's receipt screen)
        if display:
            display.show_receipt(
                items=transaction.get_items(),
                total=transaction.get_total()
            )
        
        # Print text summary for terminal
        print(transaction.get_summary())
        
        # Send to payment processor
        price_cents = transaction.get_total_cents()
        description = transaction.get_eport_description_multiple_items()
        
        if payment.send_transaction_result(
            quantity=len(transaction.get_items()),
            price_cents=price_cents,
            item_id="1",
            description=description
        ):
            logger.info(f"Transaction complete: {transaction.get_compact_summary()}")
        
        # Show receipt for configured timeout
        time.sleep(RECEIPT_DISPLAY_TIMEOUT)
    
    # Setup callbacks and start dispensing
    machine.start_dispensing(
        flowmeter_callback=on_flowmeter_pulse,
        done_callback=on_done_button,
        product_switch_callback=on_product_switch
    )
    
    # Main control loop with timer updates
    while not transaction_complete:
        current_time = time.time()
        
        # Update session timer on display
        if display:
            session_duration = current_time - session_start_time
            seconds_remaining = int(DISPENSING_MAX_SESSION_TIME - session_duration)
            
            inactivity = current_time - last_activity_time
            warning = inactivity > INACTIVITY_WARNING_TIME
            
            display.update_timer(seconds_remaining, warning=warning)
        
        # ... existing timeout and motor control logic ...
        
        time.sleep(MOTOR_CONTROL_LOOP_DELAY)
```

---

## Deployment Setup

### 1. Install Dependencies

```bash
cd ~/soap
pip3 install flask flask-socketio python-socketio
```

### 2. Install Chromium Browser

```bash
sudo apt update
sudo apt install chromium-browser unclutter
```

### 3. Configure Chromium Kiosk Mode

Create autostart script:

```bash
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

Add these lines:

```bash
# Hide mouse cursor
@unclutter -idle 0

# Start Chromium in kiosk mode
@chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --check-for-update-interval=31536000 http://localhost:5000
```

### 4. Enable X Server (if headless)

```bash
# Allow X server to start without login
sudo raspi-config
# Navigate to: Boot Options → Desktop/CLI → Desktop Autologin
```

### 5. Test Display

```bash
# Start the vending machine controller
python3 -m ePort.main

# In another terminal, check display server
curl http://localhost:5000

# Open browser manually to test
chromium-browser --kiosk http://localhost:5000
```

---

## Implementation Phases

### Phase 1: Flask Server & Basic HTML (Week 1)
- [ ] Create DisplayServer class (`src/display_server.py`)
- [ ] Setup Flask app with WebSocket support
- [ ] Create HTML templates for all 7 states
- [ ] Add basic CSS styling
- [ ] Test state transitions via API

**Deliverables:**
- Working Flask server on port 5000
- All HTML templates rendering
- Manual state switching via curl/Postman

---

### Phase 2: Real-Time Updates (Week 2)
- [ ] Implement WebSocket event handlers
- [ ] Add JavaScript client (`static/app.js`)
- [ ] Real-time product counter updates
- [ ] Timer countdown display
- [ ] Test with mock data

**Deliverables:**
- Live counter updates without page refresh
- Smooth transitions between states
- Timer displays correctly

---

### Phase 3: Integration with main.py (Week 3)
- [ ] Add display server initialization in main.py
- [ ] Update `handle_dispensing()` to call display methods
- [ ] Connect flowmeter pulses to display updates
- [ ] Connect product switches to display
- [ ] Connect done button to receipt display

**Deliverables:**
- Display updates during actual dispensing
- Real transactions show on screen
- All 7 states working in production

---

### Phase 4: Artist's Vision & Polish (Week 4)
- [ ] Match artist's sketch precisely (container visual, layout)
- [ ] Create/source graphics (card icon, container, red line, buttons)
- [ ] Add CSS animations (pulse, blink, fade)
- [ ] Optimize for Raspberry Pi performance
- [ ] Add graceful fallback (display server down = terminal only)
- [ ] Owner documentation for CSS customization

**Deliverables:**
- Production-ready display matching artist's vision
- Graphics and branding in place
- Performance tested on Pi 4
- Documentation for owner updates

---

## Media Content Requirements

### Specifications

| State | Type | Resolution | Duration | File Size |
|-------|------|------------|----------|-----------|
| idle | GIF/MP4 | 1920x1080 | 5-10s loop | < 5MB |
| authorizing | GIF | 1920x1080 | 2-5s loop | < 2MB |
| ready | PNG | 1920x1080 | Static | < 1MB |
| dispensing | MP4 | 1920x1080 | 5-10s loop | < 10MB |
| complete | GIF | 1920x1080 | 3-5s | < 3MB |
| error | PNG | 1920x1080 | Static | < 1MB |

### Design Guidelines
- **High contrast** - Visible in bright/dim environments
- **Clear text** - Minimum 36pt font
- **Simple animations** - Easy to understand at a glance
- **Brand consistent** - Match store branding colors
- **Optimized size** - Fast loading on Raspberry Pi

---

## Edge Cases & Error Handling

### Missing Media File
**Behavior:** Fall back to text-only display, log warning

### Video Playback Failure
**Behavior:** Show static image, continue transaction

### Display Hardware Disconnected
**Behavior:** Continue operation with terminal output only

### Invalid Config Format
**Behavior:** Use default hardcoded state config, log error

---

## Testing Strategy

### Unit Tests
- DisplayManager initialization
- Config file parsing and validation
- Media file loading
- State transitions

### Integration Tests
- Display updates during transaction flow
- Text overlay rendering
- Transaction info updates
- Graceful degradation (no display hardware)

### Hardware Tests
- All media types render correctly
- Video loops smoothly
- Text is legible on physical display
- Performance on Raspberry Pi

---

## Performance Considerations

### Raspberry Pi Optimization
- **Pre-load media** - Load all media files at startup
- **Limit video resolution** - 1080p max, consider 720p
- **Compress videos** - Use H.264 codec, moderate bitrate
- **GIF optimization** - Reduce colors, optimize frames
- **Cache rendered text** - Don't re-render same text

### Memory Management
- Max 100MB total media files
- Unload unused media after timeout
- Monitor GPU memory usage

---

## Migration Strategy

### Backward Compatibility
Display is **optional** - system works without display hardware:
- If DISPLAY_ENABLED = False → terminal output only
- If display hardware not found → fall back to terminal
- All display calls wrapped in try/except

### Deployment
1. Install display hardware (HDMI monitor)
2. Install pygame: `pip install pygame opencv-python`
3. Add media files to `/Users/travops/soap/ePort/media/`
4. Add display_config.json to config/
5. Set DISPLAY_ENABLED = True
6. Restart service

---

## Success Metrics

### Functional
- ✅ Display shows correct content for each state
- ✅ Videos/GIFs loop smoothly
- ✅ Transaction info updates in real-time
- ✅ Graceful fallback to terminal if display fails

### Performance
- ⏱️ State transition < 0.5 seconds
- ⏱️ Video playback > 24 FPS
- 💾 Memory usage < 150MB

### User Experience
- 📊 Customer confusion reduced (measure support calls)
- 📊 Faster transaction times
- 📊 Fewer abandoned transactions

---

## Future Enhancements

- [ ] Multi-language support (swap media per language)
- [ ] Promotional video during idle
- [ ] QR code display for app download
- [ ] Real-time product availability display
- [ ] Touch screen support (future hardware)

---

## Dependencies

### Required
```txt
pygame>=2.1.0         # Display rendering
opencv-python>=4.5.0  # Video playback
Pillow>=9.0.0         # Image processing
```

### Optional
```txt
python-vlc>=3.0.0     # Alternative video player
PyQt5>=5.15.0         # Alternative display framework
```

---

## Example Usage

### Simple State Display
```python
display = DisplayManager(
    config_path="/path/to/display_config.json",
    media_dir="/path/to/media/"
)

# Show idle state
display.show_state("idle")

# Show authorizing with text
display.show_state("authorizing")

# Show product selection
display.show_state("ready")
```

### With Transaction Info
```python
# During dispensing
transaction_items = [
    {"name": "Hand Soap", "quantity": 2.5, "unit": "oz", "price": 0.38}
]
display.update_transaction_info(transaction_items, total=0.38)

# Transaction complete
display.show_state("complete")
display.show_text("Total: $0.38\nThank you!", overlay=True)
```

---

**Document Status:** Ready for Review  
**Dependencies:** None (standalone system)  
**Next Steps:** Review → Approve → Begin Phase 1
