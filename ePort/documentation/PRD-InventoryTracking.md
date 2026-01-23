# Product Requirements Document: Inventory Tracking System

**Version:** 1.0  
**Status:** Draft  
**Date:** January 2026  
**Related:** PRD-MultiProduct.md, PRD-CentralizedLogging.md

---

## Executive Summary

Implement a SQLite-based inventory tracking system that monitors product levels, alerts when refills are needed, and maintains a complete transaction history for analytics and troubleshooting.

---

## Problem Statement

**Current State:**
- No visibility into product levels
- Can't predict when refills are needed
- No historical data on usage patterns
- Manual tracking required (error-prone)
- Reactive refills (only when empty)

**Desired State:**
- Real-time inventory levels per product
- Automatic low-inventory alerts
- Proactive refill scheduling
- Historical usage data for analytics
- Persistent state across reboots/power loss

---

## Goals & Non-Goals

### Goals
1. ✅ Track current inventory level per product
2. ✅ Persist state across reboots (SQLite database)
3. ✅ Alert when inventory falls below threshold
4. ✅ Record all transactions for history/analytics
5. ✅ Support manual refill recording
6. ✅ Calculate usage rates and predict refill dates

### Non-Goals
- ❌ Automatic physical refill (hardware not available)
- ❌ Real-time remote monitoring (see PRD-CentralizedLogging)
- ❌ Customer purchase history (privacy concerns)
- ❌ Predictive maintenance (future enhancement)

---

## User Stories

### US-1: Owner Receives Low Inventory Alert
**As a** machine owner  
**I want to** receive an alert when product inventory is low  
**So that** I can refill before running out

**Acceptance Criteria:**
- Alert triggered when inventory < threshold (e.g., 20%)
- Alert includes: product name, current level, estimated days remaining
- Alert sent via log (can be picked up by centralized logging)
- Configurable threshold per product

---

### US-2: Owner Records Refill
**As a** machine owner  
**I want to** record when I refill a product  
**So that** the system tracks accurate inventory levels

**Acceptance Criteria:**
- Simple command or button to record refill
- Specify product and amount added
- System updates current inventory level
- Refill event logged with timestamp

---

### US-3: Owner Views Inventory Status
**As a** machine owner  
**I want to** view current inventory levels for all products  
**So that** I know what needs refilling

**Acceptance Criteria:**
- Display shows all products with current levels
- Shows percentage remaining
- Shows estimated days until empty
- Color-coded status (green/yellow/red)

---

### US-4: Owner Reviews Usage History
**As a** machine owner  
**I want to** view historical usage data  
**So that** I can understand usage patterns and optimize refill schedules

**Acceptance Criteria:**
- View total dispensed per product (daily, weekly, monthly)
- View average transaction size
- View busiest times/days
- Export data for analysis

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                  (Orchestration)                        │
└──────────┬──────────────────────────────┬───────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────┐
│  InventoryManager    │      │   ProductManager         │
│  (New Class)         │      │   (Existing)             │
├──────────────────────┤      └──────────────────────────┘
│ - record_dispense()  │
│ - record_refill()    │               ▼
│ - get_level()        │      ┌──────────────────────────┐
│ - check_alerts()     │      │   TransactionTracker     │
│ - get_history()      │      │   (Existing)             │
└──────┬───────────────┘      └──────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                    SQLite Database                       │
│                  inventory.db                            │
├──────────────────────────────────────────────────────────┤
│  Tables:                                                 │
│  - products (id, name, capacity, current, threshold)     │
│  - transactions (id, timestamp, product_id, amount, $)   │
│  - refills (id, timestamp, product_id, amount_added)     │
│  - alerts (id, timestamp, product_id, type, resolved)    │
└──────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: inventory_products

Stores current inventory state for each product

```sql
CREATE TABLE inventory_products (
    product_id TEXT PRIMARY KEY,           -- Links to products.json
    capacity_oz REAL NOT NULL,             -- Total capacity in ounces
    current_oz REAL NOT NULL,              -- Current level in ounces
    low_threshold_pct INTEGER DEFAULT 20,  -- Alert threshold (percentage)
    last_refill_date TEXT,                 -- ISO 8601 timestamp
    total_dispensed_oz REAL DEFAULT 0.0,   -- Total dispensed since install
    created_at TEXT NOT NULL,              -- ISO 8601 timestamp
    updated_at TEXT NOT NULL               -- ISO 8601 timestamp
);
```

**Example:**
```sql
INSERT INTO inventory_products VALUES (
    'soap_hand',      -- product_id
    640.0,            -- capacity_oz (5 gallon tank)
    450.5,            -- current_oz
    20,               -- low_threshold_pct
    '2026-01-20T10:30:00Z',  -- last_refill_date
    189.5,            -- total_dispensed_oz
    '2026-01-15T08:00:00Z',  -- created_at
    '2026-01-23T14:30:00Z'   -- updated_at
);
```

---

### Table: dispense_transactions

Records every dispensing transaction

```sql
CREATE TABLE dispense_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,               -- ISO 8601 timestamp
    product_id TEXT NOT NULL,              -- Product dispensed
    amount_oz REAL NOT NULL,               -- Amount dispensed
    price_cents INTEGER NOT NULL,          -- Price charged
    transaction_id TEXT,                   -- ePort transaction ID (if available)
    FOREIGN KEY (product_id) REFERENCES inventory_products(product_id)
);

CREATE INDEX idx_dispense_timestamp ON dispense_transactions(timestamp);
CREATE INDEX idx_dispense_product ON dispense_transactions(product_id);
```

**Example:**
```sql
INSERT INTO dispense_transactions VALUES (
    NULL,                      -- id (auto-increment)
    '2026-01-23T14:30:15Z',   -- timestamp
    'soap_hand',               -- product_id
    2.5,                       -- amount_oz
    38,                        -- price_cents
    'TXN123456789'            -- transaction_id
);
```

---

### Table: refill_events

Records manual refill operations

```sql
CREATE TABLE refill_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,               -- ISO 8601 timestamp
    product_id TEXT NOT NULL,              -- Product refilled
    amount_added_oz REAL NOT NULL,         -- Amount added
    new_level_oz REAL NOT NULL,            -- Level after refill
    notes TEXT,                            -- Optional notes
    FOREIGN KEY (product_id) REFERENCES inventory_products(product_id)
);

CREATE INDEX idx_refill_timestamp ON refill_events(timestamp);
CREATE INDEX idx_refill_product ON refill_events(product_id);
```

**Example:**
```sql
INSERT INTO refill_events VALUES (
    NULL,                      -- id (auto-increment)
    '2026-01-23T09:00:00Z',   -- timestamp
    'soap_hand',               -- product_id
    320.0,                     -- amount_added_oz (2.5 gallons)
    640.0,                     -- new_level_oz (filled to capacity)
    'Full refill - 2.5 gal'   -- notes
);
```

---

### Table: inventory_alerts

Tracks low inventory alerts and their resolution

```sql
CREATE TABLE inventory_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,               -- ISO 8601 timestamp
    product_id TEXT NOT NULL,              -- Product with low inventory
    alert_type TEXT NOT NULL,              -- 'low_inventory', 'critical_inventory', 'empty'
    level_oz REAL NOT NULL,                -- Level when alert triggered
    level_pct INTEGER NOT NULL,            -- Percentage remaining
    resolved INTEGER DEFAULT 0,            -- 0 = active, 1 = resolved
    resolved_at TEXT,                      -- When resolved (refill)
    FOREIGN KEY (product_id) REFERENCES inventory_products(product_id)
);

CREATE INDEX idx_alert_resolved ON inventory_alerts(resolved);
CREATE INDEX idx_alert_product ON inventory_alerts(product_id);
```

**Example:**
```sql
INSERT INTO inventory_alerts VALUES (
    NULL,                      -- id (auto-increment)
    '2026-01-22T16:45:00Z',   -- timestamp
    'soap_hand',               -- product_id
    'low_inventory',           -- alert_type
    120.5,                     -- level_oz
    18,                        -- level_pct (18% remaining)
    0,                         -- resolved (not yet)
    NULL                       -- resolved_at
);
```

---

## New Class: InventoryManager

**Location:** `/Users/travops/soap/ePort/src/inventory_manager.py`

### Responsibilities
- Initialize and manage SQLite database
- Record dispensing transactions
- Record refill events
- Calculate current inventory levels
- Check for low inventory and generate alerts
- Provide inventory status and history

### Class Definition

```python
class InventoryManager:
    def __init__(self, db_path: str, product_manager: ProductManager):
        """
        Initialize inventory manager
        
        Args:
            db_path: Path to SQLite database file
            product_manager: ProductManager instance for product info
        """
        self.db_path = db_path
        self.product_manager = product_manager
        self.conn = None
        self._init_database()
    
    def _init_database(self) -> None:
        """Create database and tables if they don't exist"""
    
    def record_dispense(self, product_id: str, amount_oz: float, 
                       price_cents: int, transaction_id: str = None) -> None:
        """
        Record a dispensing transaction
        
        Updates current inventory level and checks for alerts
        """
    
    def record_refill(self, product_id: str, amount_added_oz: float, 
                     notes: str = None) -> None:
        """
        Record a refill event
        
        Updates current inventory level and resolves alerts
        """
    
    def get_level(self, product_id: str) -> Dict:
        """
        Get current inventory level for product
        
        Returns:
            {
                'current_oz': float,
                'capacity_oz': float,
                'percentage': int,
                'status': 'ok' | 'low' | 'critical' | 'empty'
            }
        """
    
    def get_all_levels(self) -> List[Dict]:
        """Get inventory levels for all products"""
    
    def check_alerts(self) -> List[Dict]:
        """
        Check for low inventory and return active alerts
        
        Returns list of alerts that need attention
        """
    
    def get_usage_stats(self, product_id: str, days: int = 7) -> Dict:
        """
        Get usage statistics for product
        
        Returns:
            {
                'total_dispensed_oz': float,
                'transaction_count': int,
                'avg_transaction_oz': float,
                'daily_avg_oz': float,
                'estimated_days_remaining': int
            }
        """
    
    def get_transaction_history(self, product_id: str = None, 
                                limit: int = 100) -> List[Dict]:
        """Get recent transaction history"""
    
    def get_refill_history(self, product_id: str = None, 
                           limit: int = 50) -> List[Dict]:
        """Get refill history"""
    
    def initialize_product(self, product_id: str, capacity_oz: float, 
                          current_oz: float = None, 
                          threshold_pct: int = 20) -> None:
        """
        Initialize inventory tracking for a product
        
        Called when product is first added to system
        """
    
    def close(self) -> None:
        """Close database connection"""
```

---

## Configuration

### Add to config/__init__.py

```python
# Inventory tracking configuration
INVENTORY_DB_PATH = '/Users/travops/soap/ePort/data/inventory.db'
INVENTORY_ENABLED = True

# Default product capacities (in ounces)
DEFAULT_PRODUCT_CAPACITY_OZ = 640.0  # 5 gallons = 640 oz
DEFAULT_LOW_THRESHOLD_PCT = 20       # Alert when below 20%
CRITICAL_THRESHOLD_PCT = 10          # Critical alert at 10%

# Alert configuration
INVENTORY_CHECK_INTERVAL = 300  # Check for alerts every 5 minutes
ALERT_COOLDOWN_HOURS = 24       # Don't re-alert for same product within 24 hours
```

---

## Integration with Existing Code

### Modify main.py

```python
from .src.inventory_manager import InventoryManager
from .config import INVENTORY_DB_PATH, INVENTORY_ENABLED

# In main() function, after ProductManager initialization:
if INVENTORY_ENABLED:
    inventory = InventoryManager(INVENTORY_DB_PATH, product_manager)
    logger.info("Inventory tracking enabled")
else:
    inventory = None
    logger.info("Inventory tracking disabled")

# In handle_dispensing(), after successful transaction:
if inventory:
    try:
        inventory.record_dispense(
            product_id=current_product.id,
            amount_oz=ounces,
            price_cents=price_cents,
            transaction_id=transaction_id
        )
        
        # Check for low inventory alerts
        alerts = inventory.check_alerts()
        for alert in alerts:
            logger.warning(
                f"LOW INVENTORY: {alert['product_name']} at "
                f"{alert['level_pct']}% ({alert['level_oz']:.1f} oz)"
            )
    except Exception as e:
        logger.error(f"Failed to record inventory: {e}")
        # Don't fail transaction if inventory tracking fails
```

---

## Refill Process

### Option 1: Command Line Tool

```bash
# Refill a product
python3 -m ePort.tools.refill --product soap_hand --amount 320 --notes "2.5 gallon refill"

# View inventory status
python3 -m ePort.tools.inventory status

# View history
python3 -m ePort.tools.inventory history --product soap_hand --days 30
```

### Option 2: GPIO Button (Future)

- Add dedicated "Refill" button on machine
- Press button, select product, enter amount
- System records refill automatically

### Option 3: Web Interface (Future)

- Simple web UI on Raspberry Pi
- View status, record refills
- View charts and analytics

**Recommendation:** Start with Option 1 (CLI tool), add Option 2/3 later

---

## Alert Levels

### Alert Types

| Level | Threshold | Action | Example |
|-------|-----------|--------|---------|
| **OK** | > 20% | None | "Hand Soap: 450 oz (70%)" |
| **LOW** | 10-20% | Warning log | "⚠️ Hand Soap low: 100 oz (15%)" |
| **CRITICAL** | 5-10% | Error log + notification | "🚨 Hand Soap critical: 50 oz (8%)" |
| **EMPTY** | < 5% | Disable product | "❌ Hand Soap empty: 20 oz (3%)" |

### Alert Behavior

1. **First alert**: Log warning, create alert record
2. **Cooldown period**: Don't re-alert for 24 hours (configurable)
3. **Escalation**: If not resolved, escalate to critical
4. **Resolution**: Automatically resolve when refilled above threshold
5. **Notification**: Can be picked up by centralized logging system

---

## Usage Analytics

### Metrics to Track

1. **Daily Usage**
   - Total ounces dispensed per product per day
   - Number of transactions per day
   - Average transaction size

2. **Usage Patterns**
   - Busiest hours/days
   - Seasonal trends
   - Product popularity

3. **Refill Optimization**
   - Average days between refills
   - Predicted next refill date
   - Optimal refill schedule

4. **Revenue Tracking**
   - Total revenue per product
   - Revenue per ounce
   - Daily/weekly/monthly totals

### Example Queries

```python
# Get daily usage for last 7 days
stats = inventory.get_usage_stats('soap_hand', days=7)
print(f"Average daily usage: {stats['daily_avg_oz']:.1f} oz")
print(f"Estimated days remaining: {stats['estimated_days_remaining']}")

# Get all active alerts
alerts = inventory.check_alerts()
for alert in alerts:
    print(f"{alert['product_name']}: {alert['level_pct']}% remaining")

# Get transaction history
history = inventory.get_transaction_history('soap_hand', limit=10)
for txn in history:
    print(f"{txn['timestamp']}: {txn['amount_oz']:.2f} oz - ${txn['price_cents']/100:.2f}")
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create InventoryManager class
- [ ] Implement SQLite database schema
- [ ] Add record_dispense() and record_refill() methods
- [ ] Add get_level() and get_all_levels() methods
- [ ] Write unit tests

### Phase 2: Integration (Week 2)
- [ ] Integrate with main.py dispensing flow
- [ ] Add inventory recording after each transaction
- [ ] Initialize inventory for existing products
- [ ] Test on hardware

### Phase 3: Alerts & Monitoring (Week 3)
- [ ] Implement check_alerts() method
- [ ] Add alert generation logic
- [ ] Add alert cooldown mechanism
- [ ] Test alert thresholds

### Phase 4: CLI Tools & History (Week 4)
- [ ] Create refill CLI tool
- [ ] Create inventory status CLI tool
- [ ] Implement usage statistics
- [ ] Add transaction/refill history queries
- [ ] Documentation

### Phase 5: Advanced Features (Future)
- [ ] Web UI for inventory management
- [ ] Export to CSV/Excel
- [ ] Predictive analytics
- [ ] Integration with centralized logging
- [ ] Automatic refill ordering

---

## Data Retention

### Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Current inventory | Forever | Always needed |
| Transactions (recent) | 90 days | Analytics, troubleshooting |
| Transactions (archive) | 1 year | Tax records, trends |
| Refill events | Forever | Maintenance history |
| Resolved alerts | 30 days | Historical context |

### Database Maintenance

```python
# Run monthly cleanup
def cleanup_old_data():
    # Archive transactions older than 90 days
    # Delete resolved alerts older than 30 days
    # Vacuum database to reclaim space
```

---

## Error Handling

### Failure Scenarios

1. **Database write fails**
   - Log error, continue transaction
   - Don't fail customer transaction due to inventory tracking
   - Retry write in background

2. **Database corrupted**
   - Restore from backup (daily backups recommended)
   - Reinitialize from products.json if no backup
   - Log critical error

3. **Negative inventory**
   - Log warning (calibration issue or missed refill)
   - Allow transaction to proceed
   - Alert owner to check and correct

4. **Product not initialized**
   - Auto-initialize with default capacity
   - Log warning for owner to set correct capacity

---

## Testing Strategy

### Unit Tests
- Database initialization and schema creation
- Record dispense and verify inventory update
- Record refill and verify level increase
- Alert generation at thresholds
- Usage statistics calculations
- Transaction history queries

### Integration Tests
- Full transaction flow with inventory recording
- Multiple products dispensing
- Refill process
- Alert cooldown behavior
- Database persistence across restarts

### Edge Cases
- Dispense more than current inventory (negative)
- Refill beyond capacity (overflow)
- Concurrent transactions (SQLite handles this)
- Database file locked
- Power loss during write (SQLite atomic)

---

## Security & Privacy

### Data Protection

1. **No customer PII**
   - Don't store card numbers
   - Don't store customer names
   - Transaction IDs are anonymized

2. **File Permissions**
   - Database file: 600 (owner read/write only)
   - Backup files: 600
   - No world-readable data

3. **Backup Strategy**
   - Daily automated backups
   - Keep 7 daily backups
   - Store backups in separate directory
   - Optional: Sync to remote server (encrypted)

---

## CLI Tool Examples

### Refill Tool

```bash
# Full refill
$ python3 -m ePort.tools.refill soap_hand 320
✅ Refilled Hand Soap: +320.0 oz → 640.0 oz (100%)

# Partial refill with notes
$ python3 -m ePort.tools.refill soap_dish 160 --notes "Half tank refill"
✅ Refilled Dish Soap: +160.0 oz → 320.0 oz (50%)

# Interactive mode
$ python3 -m ePort.tools.refill
Select product:
  1. Hand Soap (current: 120 oz, 18%)
  2. Dish Soap (current: 450 oz, 70%)
Choice: 1
Amount to add (oz): 520
Notes (optional): Full 5-gallon refill
✅ Refilled Hand Soap: +520.0 oz → 640.0 oz (100%)
```

### Status Tool

```bash
# View all products
$ python3 -m ePort.tools.inventory status
INVENTORY STATUS
─────────────────────────────────────────────────
Hand Soap:    450.0 oz / 640.0 oz (70%) ✅ OK
Dish Soap:    100.0 oz / 640.0 oz (15%) ⚠️  LOW
Detergent:     50.0 oz / 640.0 oz (8%)  🚨 CRITICAL
─────────────────────────────────────────────────

ACTIVE ALERTS:
⚠️  Dish Soap below 20% threshold (15% remaining)
🚨 Detergent below 10% threshold (8% remaining)

# View specific product with stats
$ python3 -m ePort.tools.inventory status soap_hand
HAND SOAP
─────────────────────────────────────────────────
Current:      450.0 oz (70% of 640.0 oz)
Status:       ✅ OK
Last Refill:  2026-01-20 10:30:00 (3 days ago)

USAGE (Last 7 days):
  Total:      189.5 oz
  Avg/day:    27.1 oz
  Avg/txn:    2.3 oz
  Txn count:  83

FORECAST:
  Days remaining: ~16 days
  Next refill:    ~2026-02-08
```

### History Tool

```bash
# Recent transactions
$ python3 -m ePort.tools.inventory history soap_hand --limit 5
TRANSACTION HISTORY - HAND SOAP
─────────────────────────────────────────────────
2026-01-23 14:30:15  2.50 oz  $0.38
2026-01-23 14:15:42  3.20 oz  $0.48
2026-01-23 13:45:10  1.80 oz  $0.27
2026-01-23 13:22:33  2.10 oz  $0.32
2026-01-23 12:58:19  4.50 oz  $0.68

# Refill history
$ python3 -m ePort.tools.inventory refills
REFILL HISTORY
─────────────────────────────────────────────────
2026-01-20 10:30:00  Hand Soap    +320.0 oz → 640.0 oz
2026-01-15 09:15:00  Dish Soap    +320.0 oz → 640.0 oz
2026-01-12 14:45:00  Hand Soap    +320.0 oz → 640.0 oz
```

---

## Success Metrics

### Functional Metrics
- ✅ Inventory levels accurate within 5%
- ✅ Zero lost transactions due to inventory tracking
- ✅ Alerts generated at correct thresholds
- ✅ Database survives power loss without corruption

### Operational Metrics
- 📊 Reduce "out of stock" events by 90%
- 📊 Optimize refill schedule (reduce trips by 30%)
- 📊 Predict refills 3-5 days in advance
- 📊 Track usage trends month-over-month

---

## Future Enhancements

### Phase 2 Features
- [ ] Web dashboard for inventory management
- [ ] Mobile app for refill recording
- [ ] Automatic refill ordering (API integration)
- [ ] Predictive analytics (ML-based forecasting)
- [ ] Multi-machine inventory aggregation
- [ ] Cost tracking (product cost vs revenue)
- [ ] Waste tracking (expired product)

---

## Open Questions

### Q1: Initial Inventory Levels
**Question:** How to set initial inventory when first deploying?  
**Options:**
- Manual entry via CLI
- Assume full capacity
- Require refill event to initialize

**Recommendation:** Assume full capacity on first run, allow manual correction

---

### Q2: Calibration Drift
**Question:** What if flowmeter calibration drifts over time?  
**Solution:** 
- Track "expected vs actual" on refills
- Alert if discrepancy > 10%
- Provide recalibration tool

---

### Q3: Backup Strategy
**Question:** How to backup database?  
**Options:**
- Daily cron job copying to backup directory
- Sync to cloud storage (Dropbox, S3)
- Include in centralized logging system

**Recommendation:** Daily local backup + optional cloud sync

---

## Dependencies

### Python Packages
```txt
# Already included in Python standard library
sqlite3  # Database
datetime  # Timestamps
```

### Database
- SQLite 3.x (built into Python)
- Database file: ~1-10 MB (depends on transaction volume)

---

## Summary

**Key Takeaways:**

1. **SQLite for Reliability:** ACID compliance ensures data integrity
2. **Transaction History:** Complete audit trail for analytics
3. **Proactive Alerts:** Prevent "out of stock" situations
4. **Simple Integration:** Minimal changes to existing code
5. **CLI Tools:** Easy refill recording and status checking
6. **Future-Ready:** Foundation for advanced analytics and automation

This inventory tracking system provides visibility into product levels without requiring WiFi or external services, while setting the foundation for future centralized monitoring via the logging system.

---

**Document Status:** Ready for Review  
**Implementation Complexity:** Medium (2-3 weeks)  
**Dependencies:** PRD-MultiProduct.md (Phase 1 complete)  
**Next Steps:** Review → Approve → Phase 1 Implementation
