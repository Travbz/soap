# ePort Cellular Notifications Guide

**Purpose:** Leverage ePort's built-in cellular connection for inventory alerts and system notifications  
**Status:** Technical Reference  
**Date:** January 2026

---

## Overview

The ePort device has a built-in cellular modem that connects to payment processors. This same cellular connection can be used to send notifications, alerts, and status data to remote servers without requiring WiFi on the Raspberry Pi.

---

## How ePort Cellular Works

### Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Raspberry Pi                           │
│              (No WiFi Required)                         │
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  Vending Machine Controller                  │     │
│  │  - Inventory tracking                        │     │
│  │  - Alert generation                          │     │
│  │  - Data formatting                           │     │
│  └──────────────┬───────────────────────────────┘     │
│                 │ USB/Serial                           │
└─────────────────┼──────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  ePort Device  │
         │  (Cellular)    │
         └────────┬───────┘
                  │ 4G/LTE
                  ▼
         ┌────────────────┐
         │  USAT Server   │
         │  (USALive)     │
         └────────┬───────┘
                  │
                  ├─► Email Alerts
                  ├─► FTP/File Transfer
                  └─► Web Dashboard
```

### Key Points

- **Independent Connection:** ePort has its own cellular modem
- **No Pi WiFi Needed:** Raspberry Pi operates offline
- **Cellular Coverage Required:** Machine location must have cell signal
- **USAT Service Plan:** Active cellular plan required

---

## Available Communication Methods

### Method 1: Configuration Data Upload

**Purpose:** Send key-value configuration/status data to USAT server

**Capabilities:**
- Send machine status
- Report inventory levels
- Upload error logs
- Track usage statistics

**Access:** View data in USALive web portal

**Best For:**
- Periodic status updates
- Dashboard monitoring
- Historical reporting

---

### Method 2: File Transfer

**Purpose:** Send files to USAT server for forwarding

**Specifications:**
- **Format:** ASCII text files
- **Size Limit:** 900 bytes maximum
- **Delivery:** Email, FTP, or other transport
- **Requires:** USAT Technical Support coordination

**Best For:**
- Alert notifications
- Detailed logs
- Batch data uploads

---

### Method 3: Time Synchronization

**Purpose:** Get current time from ePort (bonus feature)

**Use Case:** Keep Pi clock synchronized without NTP

---

## Use Cases for Notifications

### 1. Low Inventory Alerts

**Scenario:** Product running low, need refill

**Implementation:**
```python
# Track inventory after each dispense
if product.remaining_ounces < LOW_THRESHOLD:
    alert = f"LOW_INVENTORY:{product.id}:{product.remaining_ounces}"
    eport.send_alert(alert)
```

**Alert Content:**
- Product ID
- Remaining quantity
- Timestamp
- Machine location

---

### 2. Hardware Errors

**Scenario:** Motor failure, flowmeter malfunction

**Implementation:**
```python
try:
    machine.control_motor(True)
except MachineHardwareError as e:
    alert = f"HARDWARE_ERROR:MOTOR:{str(e)}"
    eport.send_alert(alert)
```

**Alert Content:**
- Error type
- Component affected
- Error message
- Timestamp

---

### 3. Payment Issues

**Scenario:** Multiple declined cards, ePort connectivity issues

**Implementation:**
```python
if consecutive_declines > MAX_DECLINES:
    alert = f"PAYMENT_ISSUE:DECLINES:{consecutive_declines}"
    eport.send_alert(alert)
```

**Alert Content:**
- Issue type
- Frequency/count
- Last occurrence
- Status code

---

### 4. Daily Sales Reports

**Scenario:** End-of-day transaction summary

**Implementation:**
```python
def send_daily_report():
    report = {
        "date": today,
        "transactions": transaction_count,
        "revenue": total_revenue,
        "products_dispensed": product_summary
    }
    eport.send_report(report)
```

**Report Content:**
- Transaction count
- Total revenue
- Products dispensed
- Average transaction value

---

### 5. Machine Status Heartbeat

**Scenario:** Periodic "I'm alive" signal

**Implementation:**
```python
# Every hour
def send_heartbeat():
    status = {
        "timestamp": now,
        "uptime": system_uptime,
        "status": "operational",
        "last_transaction": last_transaction_time
    }
    eport.send_status(status)
```

**Status Content:**
- Machine operational
- Uptime
- Last transaction time
- System health

---

## Implementation Strategy

### Phase 1: Basic Inventory Tracking

**Goal:** Track product levels, send alerts when low

**Components:**
1. Add inventory tracking to ProductManager
2. Decrement inventory after each dispense
3. Check threshold after each transaction
4. Send alert via ePort when low

**Code Structure:**
```python
# ePort/src/inventory.py
class InventoryTracker:
    def __init__(self, products: List[Product]):
        self.inventory = {p.id: p.initial_quantity for p in products}
    
    def decrement(self, product_id: str, quantity: float):
        self.inventory[product_id] -= quantity
    
    def get_remaining(self, product_id: str) -> float:
        return self.inventory[product_id]
    
    def is_low(self, product_id: str, threshold: float) -> bool:
        return self.inventory[product_id] < threshold
```

---

### Phase 2: ePort Alert Protocol

**Goal:** Implement ePort commands for sending alerts

**Research Needed:**
- Contact USAT Technical Support
- Get documentation for config upload commands
- Understand data format requirements
- Set up USALive portal access

**Protocol Implementation:**
```python
# ePort/src/payment.py - Add to EPortProtocol class

def send_config_data(self, key: str, value: str) -> bool:
    """
    Send configuration data to USAT server
    
    Args:
        key: Configuration key (e.g., "LOW_INVENTORY")
        value: Configuration value (e.g., "soap_hand:50oz")
    
    Returns:
        True if sent successfully
    """
    # Command format: TBD - requires USAT documentation
    # Example: "CONFIG" + RS + key + RS + value + CRC + CR
    pass

def send_file(self, filename: str, content: str) -> bool:
    """
    Send file to USAT server (max 900 bytes)
    
    Args:
        filename: File identifier
        content: ASCII file content (max 900 bytes)
    
    Returns:
        True if sent successfully
    """
    if len(content) > 900:
        raise ValueError("File content exceeds 900 byte limit")
    
    # Command format: TBD - requires USAT documentation
    pass
```

---

### Phase 3: Alert Manager

**Goal:** Centralized alert handling and formatting

**Code Structure:**
```python
# ePort/src/alerts.py

class AlertManager:
    def __init__(self, eport: EPortProtocol):
        self.eport = eport
        self.alert_history = []
    
    def send_low_inventory_alert(self, product_id: str, remaining: float):
        """Send low inventory alert"""
        alert_data = f"LOW_INVENTORY|{product_id}|{remaining}|{datetime.now()}"
        self.eport.send_config_data("ALERT", alert_data)
        self.alert_history.append(("LOW_INVENTORY", alert_data))
    
    def send_hardware_error(self, component: str, error: str):
        """Send hardware error alert"""
        alert_data = f"HARDWARE_ERROR|{component}|{error}|{datetime.now()}"
        self.eport.send_config_data("ALERT", alert_data)
        self.alert_history.append(("HARDWARE_ERROR", alert_data))
    
    def send_daily_report(self, report_data: Dict):
        """Send daily sales report"""
        # Format as compact string (max 900 bytes)
        report_str = self._format_report(report_data)
        self.eport.send_file("daily_report", report_str)
```

---

### Phase 4: USALive Integration

**Goal:** Configure USAT server to forward alerts

**Setup Steps:**
1. Create USALive account (if not exists)
2. Register ePort device
3. Configure alert forwarding:
   - Email notifications
   - FTP file delivery
   - Webhook endpoints (if supported)
4. Set up alert rules and thresholds

---

## Configuration

### Add to config/__init__.py

```python
# Inventory and alert configuration
LOW_INVENTORY_THRESHOLD = 100.0  # Alert when < 100 oz remaining
CRITICAL_INVENTORY_THRESHOLD = 20.0  # Critical alert when < 20 oz
INVENTORY_CHECK_INTERVAL = 3600  # Check every hour (seconds)

# Alert settings
MAX_CONSECUTIVE_DECLINES = 5  # Alert after 5 declined cards
HEARTBEAT_INTERVAL = 3600  # Send status every hour
DAILY_REPORT_TIME = "23:59"  # Send daily report at 11:59 PM

# ePort notification settings
EPORT_ALERTS_ENABLED = True  # Enable/disable ePort alerts
ALERT_RETRY_ATTEMPTS = 3  # Retry failed alerts
ALERT_RETRY_DELAY = 60  # Wait 60 seconds between retries
```

---

## Data Format Examples

### Low Inventory Alert

```
Format: LOW_INVENTORY|product_id|remaining|timestamp
Example: LOW_INVENTORY|soap_hand|45.2|2026-01-22T14:30:00Z
```

### Hardware Error Alert

```
Format: HARDWARE_ERROR|component|error_msg|timestamp
Example: HARDWARE_ERROR|MOTOR|GPIO timeout|2026-01-22T14:30:00Z
```

### Daily Report (File)

```
DAILY_REPORT|2026-01-22
TRANSACTIONS:47
REVENUE:$142.35
PRODUCTS:
  soap_hand:234.5oz|$35.18
  soap_dish:189.2oz|$22.70
  detergent:567.8oz|$84.47
ERRORS:2
UPTIME:23.5hrs
```

---

## Limitations & Considerations

### Technical Limitations

1. **900 Byte File Limit**
   - Keep alerts concise
   - Use abbreviations
   - Batch data carefully

2. **Cellular Connectivity**
   - Requires cell signal at machine location
   - May have delays in poor coverage areas
   - Data charges apply (check USAT plan)

3. **Protocol Documentation**
   - Limited public documentation
   - May require USAT support for implementation
   - Commands may vary by ePort firmware version

4. **No Real-Time Guarantees**
   - Cellular delays possible
   - Not suitable for time-critical alerts
   - Consider as "best effort" delivery

### Operational Considerations

1. **USAT Service Plan**
   - Verify data allowance
   - Understand overage charges
   - Monitor usage

2. **Alert Frequency**
   - Don't spam alerts (rate limiting)
   - Batch non-urgent notifications
   - Use appropriate thresholds

3. **Privacy & Security**
   - Don't send sensitive customer data
   - Aggregate transaction data
   - Follow PCI compliance guidelines

---

## Alternative: WiFi on Raspberry Pi

If ePort cellular is insufficient, consider adding WiFi to the Pi:

### Advantages of Pi WiFi

✅ **More Control**
- Direct API calls
- Real-time notifications
- Flexible protocols (HTTP, MQTT, etc.)

✅ **Better Integration**
- SMS via Twilio
- Email via SendGrid
- Slack/Discord webhooks
- Custom dashboards

✅ **No USAT Dependency**
- Independent of ePort service
- No 900 byte limit
- No protocol restrictions

### Disadvantages

❌ **Requires Network**
- WiFi setup at each location
- Network credentials management
- Potential connectivity issues

❌ **More Complexity**
- Additional code/dependencies
- Network error handling
- Security considerations

---

## Hybrid Approach (Recommended)

**Use both ePort cellular AND Pi WiFi:**

```python
class NotificationManager:
    def __init__(self, eport: EPortProtocol, wifi_enabled: bool):
        self.eport = eport
        self.wifi_enabled = wifi_enabled
    
    def send_alert(self, alert_type: str, data: str):
        """Send alert via available channels"""
        
        # Try WiFi first (faster, more reliable)
        if self.wifi_enabled:
            try:
                self._send_via_wifi(alert_type, data)
                return
            except Exception as e:
                logger.warning(f"WiFi alert failed: {e}")
        
        # Fallback to ePort cellular
        try:
            self._send_via_eport(alert_type, data)
        except Exception as e:
            logger.error(f"ePort alert failed: {e}")
```

**Benefits:**
- Primary: Fast WiFi notifications
- Backup: ePort cellular if WiFi down
- Redundancy for critical alerts

---

## Next Steps

### 1. Research Phase
- [ ] Contact USAT Technical Support
- [ ] Request documentation for config upload commands
- [ ] Get USALive portal access
- [ ] Understand data format requirements

### 2. Development Phase
- [ ] Implement inventory tracking (see PRD-MultiProduct.md)
- [ ] Add ePort alert commands to EPortProtocol class
- [ ] Create AlertManager class
- [ ] Add configuration options

### 3. Testing Phase
- [ ] Test alert delivery with USAT
- [ ] Verify data appears in USALive
- [ ] Test email/FTP forwarding
- [ ] Validate 900 byte limit handling

### 4. Deployment Phase
- [ ] Configure USALive portal
- [ ] Set up alert forwarding
- [ ] Deploy to production machine
- [ ] Monitor alert delivery

---

## Resources

### USAT Contact
- **Technical Support:** Contact for protocol documentation
- **USALive Portal:** https://usalive.usatech.com (account required)
- **Service Plans:** Verify data allowance with USAT

### Related Documentation
- [ePort Protocol Reference](ePort-Protocol-Reference.md) - Serial protocol details
- [PRD: Multi-Product System](PRD-MultiProduct.md) - Inventory tracking design
- [Architecture](ARCHITECTURE.md) - System overview

---

## Summary

**Key Takeaways:**

1. ✅ **ePort cellular can be used for notifications** without Pi WiFi
2. 📊 **Best for:** Inventory alerts, status updates, daily reports
3. 📝 **Limitation:** 900 byte file limit, requires USAT coordination
4. 🔄 **Hybrid approach recommended:** WiFi primary, ePort backup
5. 📞 **Next step:** Contact USAT for protocol documentation

The ePort's cellular connection provides a viable notification channel for remote monitoring without requiring WiFi infrastructure at each machine location.

---

**Document Status:** Technical Reference  
**Implementation Status:** Requires USAT protocol documentation  
**Related PRDs:** PRD-MultiProduct.md (inventory tracking)
