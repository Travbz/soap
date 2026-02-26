// WebSocket connection for real-time updates
const socket = io();

// Product data cache - dynamically populated
const productData = {};
let productList = [];

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

// Build dynamic product bar
function buildProductBar(containerId, showTotal = true) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    // Add product columns
    productList.forEach(product => {
        const col = document.createElement('div');
        col.className = 'product-column';
        col.id = `${product.id}-column`;
        
        const data = productData[product.id] || { qty: 0, price: 0 };
        
        col.innerHTML = `
            <div class="product-name">${product.name}</div>
            <div class="product-qty" id="${product.id}-qty">${data.qty.toFixed(1)}${product.unit}</div>
            <div class="product-price" id="${product.id}-price">$${data.price.toFixed(2)}</div>
        `;
        
        container.appendChild(col);
    });
    
    // Add total column if requested
    if (showTotal) {
        const totalCol = document.createElement('div');
        totalCol.className = 'product-column total-column';
        totalCol.innerHTML = `
            <div class="total-label">TOTAL:</div>
            <div class="total-amount" id="total-price">$0.00</div>
        `;
        container.appendChild(totalCol);
    }
}

// WebSocket event: Load products (sent by server)
socket.on('load_products', (data) => {
    console.log('Products loaded:', data);
    productList = data.products;
    
    // Initialize product data cache
    productList.forEach(product => {
        productData[product.id] = { qty: 0, price: 0 };
    });
    
    // Build the single persistent product bar MFE
    buildProductBar('product-bar');
    
    // Build dynamic arrows for ready and waiting screens
    buildButtonArrows();
    buildButtonArrowsWaiting();
});

// Build dynamic button arrows based on number of products
function buildButtonArrows() {
    const container = document.getElementById('button-arrows-ready');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Calculate width for products only (excluding total column)
    const productCount = productList.length;
    const totalColumns = productCount + 1; // products + total
    const productWidthPercent = (productCount / totalColumns) * 100;
    
    container.style.width = `${productWidthPercent}%`;
    
    productList.forEach(() => {
        const arrow = document.createElement('span');
        arrow.textContent = '▼';
        container.appendChild(arrow);
    });
}

// Build dynamic button arrows for waiting screen
function buildButtonArrowsWaiting() {
    const container = document.getElementById('button-arrows-waiting');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Calculate width for products only (excluding total column)
    const productCount = productList.length;
    const totalColumns = productCount + 1; // products + total
    const productWidthPercent = (productCount / totalColumns) * 100;
    
    container.style.width = `${productWidthPercent}%`;
    
    productList.forEach(() => {
        const arrow = document.createElement('span');
        arrow.textContent = '▼';
        container.appendChild(arrow);
    });
}

// WebSocket event: Change state
socket.on('change_state', (data) => {
    console.log('State change:', data.state);
    showScreen(data.state);
    
    // Reset product data only when starting new transaction (idle)
    // Do NOT reset when entering dispensing - we want to keep accumulated values
    if (data.state === 'idle') {
        resetProductData();
    }
    
    // Start countdown when showing receipt
    if (data.state === 'complete') {
        startCountdown(10);
    }
});

// WebSocket event: Update product counter
socket.on('update_product', (data) => {
    const { product_id, quantity, unit, price, is_active } = data;
    
    // Update cached data
    if (productData[product_id]) {
        productData[product_id].qty = quantity;
        productData[product_id].price = price;
    }
    
    // Update the single product bar MFE
    const qtyElement = document.getElementById(`${product_id}-qty`);
    if (qtyElement) {
        qtyElement.textContent = `${quantity.toFixed(1)}${unit}`;
    }
    
    const priceElement = document.getElementById(`${product_id}-price`);
    if (priceElement) {
        priceElement.textContent = `$${price.toFixed(2)}`;
    }
    
    // Highlight active product column only
    const column = document.getElementById(`${product_id}-column`);
    if (column) {
        if (is_active) {
            column.classList.add('active');
        } else {
            column.classList.remove('active');
        }
        // Always remove purchased class - all non-active products show original gray
        column.classList.remove('purchased');
    }
});

// WebSocket event: Update total
socket.on('update_total', (data) => {
    const totalElement = document.getElementById('total-price');
    if (totalElement) {
        totalElement.textContent = `$${data.total.toFixed(2)}`;
    }
});

// WebSocket event: Show receipt
socket.on('show_receipt', (data) => {
    const { items, subtotal, tax, total, timestamp } = data;
    
    // Populate receipt items
    const receiptItemsContainer = document.getElementById('receipt-items');
    if (receiptItemsContainer) {
        receiptItemsContainer.innerHTML = '';
        
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'receipt-item';
            
            // Calculate cents per ounce from price and quantity
            const centsPerOunce = Math.round((item.price / item.quantity) * 100);
            
            itemDiv.innerHTML = `
                <div class="receipt-item-name">${item.product_name.toUpperCase()} ----- ${centsPerOunce}¢ per ounce</div>
                <div class="receipt-item-details">${item.quantity.toFixed(1)}${item.unit}-------------------------$${item.price.toFixed(2)}</div>
            `;
            
            receiptItemsContainer.appendChild(itemDiv);
        });
    }
    
    // Update subtotal
    const receiptSubtotalElement = document.getElementById('receipt-subtotal');
    if (receiptSubtotalElement) {
        receiptSubtotalElement.textContent = (subtotal || total).toFixed(2);
    }
    
    // Update tax
    const receiptTaxRow = document.getElementById('receipt-tax-row');
    const receiptTaxElement = document.getElementById('receipt-tax');
    if (tax && tax > 0) {
        if (receiptTaxRow) receiptTaxRow.style.display = '';
        if (receiptTaxElement) receiptTaxElement.textContent = tax.toFixed(2);
    } else {
        if (receiptTaxRow) receiptTaxRow.style.display = 'none';
    }
    
    // Update total
    const receiptTotalElement = document.getElementById('receipt-total');
    if (receiptTotalElement) {
        receiptTotalElement.textContent = total.toFixed(2);
    }
    
    // Update timestamp
    const receiptTimestampElement = document.getElementById('receipt-timestamp');
    if (receiptTimestampElement) {
        receiptTimestampElement.textContent = timestamp || '';
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

// Reset product data
function resetProductData() {
    Object.keys(productData).forEach(key => {
        productData[key] = { qty: 0, price: 0 };
    });
    
    // Reset display in the single product bar MFE
    productList.forEach(product => {
        const qtyElement = document.getElementById(`${product.id}-qty`);
        if (qtyElement) {
            qtyElement.textContent = `0.0${product.unit}`;
        }
        
        const priceElement = document.getElementById(`${product.id}-price`);
        if (priceElement) {
            priceElement.textContent = '$0.00';
        }
        
        const column = document.getElementById(`${product.id}-column`);
        if (column) {
            column.classList.remove('active');
            column.classList.remove('purchased');  // Also remove purchased state
        }
    });
    
    const totalElement = document.getElementById('total-price');
    if (totalElement) {
        totalElement.textContent = '$0.00';
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
    // Reset to idle and request products on connect
    resetProductData();
    showScreen('idle');
    socket.emit('request_products');
});

socket.on('disconnect', () => {
    console.log('Disconnected from display server');
});
