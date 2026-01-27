// WebSocket connection for real-time updates
const socket = io();

// Product data cache
const productData = {
    soap_hand: { qty: 0, price: 0 },
    soap_dish: { qty: 0, price: 0 },
    soap_laundry: { qty: 0, price: 0 }
};

// Current state
let currentState = 'idle';
let countdownInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Display client initialized');
    showScreen('idle');
});

// Show specific screen, hide others
function showScreen(screenName) {
    const screens = document.querySelectorAll('.screen');
    screens.forEach(screen => {
        screen.classList.add('hidden');
    });
    
    const targetScreen = document.getElementById(`${screenName}-screen`);
    if (targetScreen) {
        targetScreen.classList.remove('hidden');
        currentState = screenName;
        console.log('Screen changed to:', screenName);
    }
}

// WebSocket event: Change state
socket.on('change_state', (data) => {
    console.log('State change:', data.state);
    showScreen(data.state);
    
    // Reset data when entering dispensing state
    if (data.state === 'dispensing') {
        resetProductData();
    }
    
    // Start countdown when showing receipt
    if (data.state === 'complete') {
        startCountdown(10);
    }
});

// WebSocket event: Update product counter
socket.on('update_product', (data) => {
    const { product_id, product_name, quantity, unit, price, is_active } = data;
    
    // Update cached data
    if (productData[product_id]) {
        productData[product_id].qty = quantity;
        productData[product_id].price = price;
    }
    
    // Update display based on product ID
    let idPrefix = '';
    if (product_id === 'soap_hand') {
        idPrefix = 'hand';
    } else if (product_id === 'soap_dish') {
        idPrefix = 'dish';
    } else if (product_id === 'soap_laundry') {
        idPrefix = 'laundry';
    }
    
    if (idPrefix) {
        // Update quantity
        const qtyElement = document.getElementById(`${idPrefix}-qty`);
        if (qtyElement) {
            qtyElement.textContent = `${quantity.toFixed(1)}${unit}`;
        }
        
        // Update price
        const priceElement = document.getElementById(`${idPrefix}-price`);
        if (priceElement) {
            priceElement.textContent = `$${price.toFixed(2)}`;
        }
        
        // Highlight active product
        const row = qtyElement ? qtyElement.parentElement : null;
        if (row) {
            if (is_active) {
                row.classList.add('active-product');
            } else {
                row.classList.remove('active-product');
            }
        }
    }
    
    // Update "Currently Dispensing" text
    if (is_active) {
        const currentProductElement = document.getElementById('current-product');
        if (currentProductElement) {
            currentProductElement.textContent = product_name;
        }
    }
});

// WebSocket event: Update total
socket.on('update_total', (data) => {
    const totalPriceElement = document.getElementById('total-price');
    if (totalPriceElement) {
        totalPriceElement.textContent = `$${data.total.toFixed(2)}`;
    }
});

// WebSocket event: Show receipt
socket.on('show_receipt', (data) => {
    const { items, total } = data;
    
    // Populate receipt items
    const receiptItemsContainer = document.getElementById('receipt-items');
    if (receiptItemsContainer) {
        receiptItemsContainer.innerHTML = '';
        
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'receipt-item';
            
            const nameSpan = document.createElement('div');
            nameSpan.className = 'receipt-item-name';
            nameSpan.textContent = `${item.product_name.toUpperCase()}`;
            
            const detailsSpan = document.createElement('div');
            detailsSpan.className = 'receipt-item-details';
            detailsSpan.textContent = `${item.quantity.toFixed(1)}${item.unit} ................ $${item.price.toFixed(2)}`;
            
            itemDiv.appendChild(nameSpan);
            itemDiv.appendChild(detailsSpan);
            receiptItemsContainer.appendChild(itemDiv);
        });
    }
    
    // Update total
    const receiptTotalElement = document.getElementById('receipt-total');
    if (receiptTotalElement) {
        receiptTotalElement.textContent = total.toFixed(2);
    }
    
    // Show complete screen
    showScreen('complete');
    startCountdown(10);
});

// WebSocket event: Show error
socket.on('show_error', (data) => {
    const messageElement = document.getElementById('error-message');
    if (messageElement && data.message) {
        messageElement.textContent = data.message;
    }
    
    const codeElement = document.getElementById('error-code');
    if (codeElement && data.code) {
        codeElement.textContent = `Error code: ${data.code}`;
    }
    
    showScreen('error');
});

// WebSocket event: Update timer
socket.on('update_timer', (data) => {
    const { seconds, warning } = data;
    const timerElement = document.getElementById('session-timer');
    
    if (timerElement) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        timerElement.textContent = `⏱️ Time remaining: ${minutes}:${secs.toString().padStart(2, '0')}`;
        
        if (warning) {
            timerElement.classList.add('warning');
        } else {
            timerElement.classList.remove('warning');
        }
    }
});

// Reset product data
function resetProductData() {
    productData.soap_hand = { qty: 0, price: 0 };
    productData.soap_dish = { qty: 0, price: 0 };
    productData.soap_laundry = { qty: 0, price: 0 };
    
    // Reset display
    ['hand', 'dish', 'laundry'].forEach(prefix => {
        const qtyElement = document.getElementById(`${prefix}-qty`);
        const priceElement = document.getElementById(`${prefix}-price`);
        
        if (qtyElement) qtyElement.textContent = '0oz';
        if (priceElement) priceElement.textContent = '$0.00';
    });
    
    const totalPriceElement = document.getElementById('total-price');
    if (totalPriceElement) {
        totalPriceElement.textContent = '$0.00';
    }
    
    const currentProductElement = document.getElementById('current-product');
    if (currentProductElement) {
        currentProductElement.textContent = '--';
    }
}

// Countdown timer for receipt screen
function startCountdown(seconds) {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    let remaining = seconds;
    const countdownElement = document.getElementById('countdown');
    
    countdownInterval = setInterval(() => {
        remaining--;
        if (countdownElement) {
            countdownElement.textContent = remaining;
        }
        
        if (remaining <= 0) {
            clearInterval(countdownInterval);
            showScreen('idle');
        }
    }, 1000);
}

// Connection status
socket.on('connect', () => {
    console.log('Connected to display server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from display server');
});
