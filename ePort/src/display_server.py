"""
Flask-based display server for customer guidance system

Provides real-time transaction updates via WebSocket to browser-based display.
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from typing import List, Dict, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class DisplayServer:
    """
    Web-based display server using Flask and WebSocket
    
    Serves HTML/CSS/JS display to Chromium browser in kiosk mode.
    Provides real-time updates for product counters, totals, and state transitions.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 5000, products: List[Dict] = None):
        """
        Initialize Flask server with WebSocket support
        
        Args:
            host: Server host address
            port: Server port number
            products: List of product dictionaries with id, name, unit, price_per_unit
        """
        self.app = Flask(__name__, 
                        template_folder='../display/templates',
                        static_folder='../display/static')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.host = host
        self.port = port
        self.current_state = "idle"
        self.products = products or []
        self._setup_routes()
        logger.info(f"DisplayServer initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.after_request
        def add_no_cache_headers(response):
            """Prevent browser caching to ensure fresh state on reload"""
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        
        @self.app.route('/')
        def index():
            """Main display page"""
            return render_template('index.html')
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'ok', 'state': self.current_state}
        
        @self.socketio.on('connect')
        def handle_connect():
            """Client connected - send initial state"""
            emit('change_state', {'state': self.current_state})
            if hasattr(self, 'products'):
                emit('load_products', {'products': self.products})
        
        @self.socketio.on('request_products')
        def handle_request_products():
            """Send product list to client"""
            if hasattr(self, 'products'):
                emit('load_products', {'products': self.products})
    
    def start(self, background: bool = True) -> None:
        """
        Start the Flask server
        
        Args:
            background: If True, run in background thread (non-blocking)
        """
        if background:
            thread = threading.Thread(
                target=lambda: self.socketio.run(
                    self.app, 
                    host=self.host, 
                    port=self.port,
                    debug=False,
                    allow_unsafe_werkzeug=True
                )
            )
            thread.daemon = True
            thread.start()
            logger.info("Display server started in background")
        else:
            self.socketio.run(self.app, host=self.host, port=self.port)
    
    def change_state(self, state: str) -> None:
        """
        Change display state
        
        Args:
            state: State name (idle, authorizing, ready, dispensing, complete, declined, error)
        """
        prev_state = self.current_state
        self.current_state = state
        self.socketio.emit('change_state', {'state': state})
        logger.info(f"[DISPLAY] State transition: {prev_state} -> {state}")
    
    def update_product(self, product_id: str, product_name: str, 
                      quantity: float, unit: str, price: float,
                      is_active: bool = False) -> None:
        """
        Update product counter in real-time
        
        Args:
            product_id: Product identifier (soap_hand, soap_dish, soap_laundry)
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
    
    def show_receipt(self, items: List[Dict], total: float,
                     subtotal: float = 0.0, tax: float = 0.0,
                     timestamp: str = '') -> None:
        """
        Show final receipt with tax and timestamp
        
        Args:
            items: List of items with {product_name, quantity, unit, price}
            total: Final transaction total (including tax)
            subtotal: Pre-tax subtotal
            tax: Tax amount in dollars
            timestamp: Formatted timestamp string (e.g., '02/25/2026 03:15 PM CST')
        """
        self.change_state('complete')
        self.socketio.emit('show_receipt', {
            'items': items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'timestamp': timestamp
        })
        logger.info(f"Receipt displayed: {len(items)} items, ${total:.2f} (tax: ${tax:.2f})")
    
    def show_error(self, error_message: str, error_code: Optional[str] = None) -> None:
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
        logger.warning(f"Error displayed: {error_message} (code: {error_code})")
    
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
