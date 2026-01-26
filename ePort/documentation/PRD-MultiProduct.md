# Product Requirements Document: Multi-Product Dispensing System

**Version:** 1.0  
**Status:** Draft  
**Date:** January 2026

---

## Executive Summary

Enable the vending machine to dispense multiple products in a single transaction, allowing customers to select different products (e.g., hand soap, dish soap, laundry detergent) and be charged the combined total on one card authorization.

---

## Problem Statement

**Current State:**
- System only supports one product type (hand wash)
- Single flowmeter tracks one dispensing operation
- No product selection mechanism
- Price calculation based on single product type

**Desired State:**
- Support multiple product types with different prices
- Allow customer to dispense multiple products in one transaction
- Charge combined total at end of transaction
- Easy to add/remove/modify products without code changes

---

## Goals & Non-Goals

### Goals
1. ✅ Support multiple products with individual pricing
2. ✅ Allow customer to dispense multiple products per transaction
3. ✅ Charge combined total at transaction end
4. ✅ Make product configuration easy (config file, not code)
5. ✅ Track individual product amounts dispensed
6. ✅ Support different units (oz, ml, etc.) per product

### Non-Goals
- ❌ Multiple simultaneous dispensing (products dispense one at a time)
- ❌ Product inventory tracking (future enhancement)
- ❌ Product recommendations or upselling
- ❌ Dynamic pricing or discounts

---

## User Stories

### US-1: Customer Selects Multiple Products
**As a** customer  
**I want to** select and dispense multiple products in one transaction  
**So that** I only swipe my card once and get charged for everything together

**Acceptance Criteria:**
- Customer can press different product buttons to select products
- Each product dispenses when its button is pressed and held
- Customer can switch between products during transaction
- Total price updates as products are dispensed

---

### US-2: Store Owner Adds New Product
**As a** company owner  
**I want to** add a new product to the machine by editing a config file  
**So that** I don't need to modify code or redeploy the application

**Acceptance Criteria:**
- New product can be added via config file (JSON/YAML)
- Product config includes: name, price per unit, unit type, GPIO pins
- Changes take effect after restart (no recompilation needed)
- Invalid config produces clear error messages

---

### US-3: Customer Sees Transaction Summary
**As a** customer  
**I want to** see what I dispensed and the total cost  
**So that** I know what I'm being charged for

**Acceptance Criteria:**
- Display shows each product name, amount, and individual cost
- Display shows total cost at end
- Receipt includes itemized list (if receipt printer available)

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
│  ProductManager      │      │   EPortProtocol          │
│  (New Class)         │      │   (Existing)             │
├──────────────────────┤      └──────────────────────────┘
│ - load_products()    │
│ - get_product(id)    │               ▼
│ - list_products()    │      ┌──────────────────────────┐
└──────┬───────────────┘      │   TransactionTracker     │
       │                      │   (New Class)            │
       │                      ├──────────────────────────┤
       │                      │ - add_item()             │
       │                      │ - get_total()            │
       │                      │ - get_summary()          │
       ▼                      └──────────────────────────┘
┌──────────────────────┐
│  Product             │
│  (New Class)         │               ▼
├──────────────────────┤      ┌──────────────────────────┐
│ - id                 │      │   MachineController      │
│ - name               │      │   (Modified)             │
│ - price_per_unit     │      ├──────────────────────────┤
│ - unit               │      │ - select_product()       │
│ - gpio_pins          │      │ - get_current_product()  │
│ - flowmeter_cal      │      └──────────────────────────┘
└──────────────────────┘
```

---

### New Classes

#### 1. ProductManager Class
**Location:** `/Users/travops/soap/ePort/src/product_manager.py`

**Responsibilities:**
- Load product definitions from config file
- Validate product configurations
- Provide product lookup by ID or button pin
- List all available products

**Key Methods:**
```python
class ProductManager:
    def __init__(self, config_path: str)
    def load_products(self) -> None
    def get_product(self, product_id: str) -> Product
    def get_product_by_button_pin(self, pin: int) -> Optional[Product]
    def list_products(self) -> List[Product]
```

---

#### 2. Product Class
**Location:** `/Users/travops/soap/ePort/src/product.py`

**Responsibilities:**
- Store product configuration data
- Provide product information

**Attributes:**
```python
class Product:
    id: str                    # Unique identifier (e.g., "soap_hand")
    name: str                  # Display name (e.g., "Hand Soap")
    description: str           # Optional description
    price_per_unit: float      # Price per unit (e.g., 0.15)
    unit: str                  # Unit type (e.g., "oz", "ml")
    motor_pin: int             # GPIO pin for motor
    flowmeter_pin: int         # GPIO pin for flowmeter
    button_pin: int            # GPIO pin for selection button
    pulses_per_unit: float     # Flowmeter calibration
```

---

#### 3. TransactionTracker Class
**Location:** `/Users/travops/soap/ePort/src/transaction_tracker.py`

**Responsibilities:**
- Track items dispensed in current transaction
- Calculate running total
- Generate transaction summary

**Key Methods:**
```python
class TransactionTracker:
    def __init__(self)
    def add_item(self, product_id: str, quantity: float, price: float) -> None
    def get_total(self) -> float
    def get_total_cents(self) -> int
    def get_items(self) -> List[Dict]
    def get_summary(self) -> str
    def reset(self) -> None
```

---

### Modified Classes

#### MachineController (Existing)
**Changes:**
- Add `select_product(product: Product)` method
- Track current product being dispensed
- Support switching between products
- Use product-specific calibration values

---

### Configuration File Format

**Location:** `/Users/travops/soap/ePort/config/products.json`

**Format Option 1: JSON**
```json
{
  "products": [
    {
      "id": "soap_hand",
      "name": "Hand Soap",
      "description": "Gentle hand wash soap",
      "price_per_unit": 0.15,
      "unit": "oz",
      "motor_pin": 17,
      "flowmeter_pin": 24,
      "button_pin": 4,
      "pulses_per_unit": 5.4
    },
    {
      "id": "soap_dish",
      "name": "Dish Soap",
      "description": "Powerful dish cleaning soap",
      "price_per_unit": 0.12,
      "unit": "oz",
      "motor_pin": 18,
      "flowmeter_pin": 25,
      "button_pin": 23,
      "pulses_per_unit": 5.2
    },
    {
      "id": "detergent_laundry",
      "name": "Laundry Detergent",
      "description": "Concentrated laundry detergent",
      "price_per_unit": 0.20,
      "unit": "oz",
      "motor_pin": 19,
      "flowmeter_pin": 26,
      "button_pin": 22,
      "pulses_per_unit": 5.6
    }
  ]
}
```

**Format Option 2: YAML** (More Human-Friendly)
```yaml
products:
  - id: soap_hand
    name: Hand Soap
    description: Gentle hand wash soap
    price_per_unit: 0.15
    unit: oz
    motor_pin: 17
    flowmeter_pin: 24
    button_pin: 4
    pulses_per_unit: 5.4

  - id: soap_dish
    name: Dish Soap
    description: Powerful dish cleaning soap
    price_per_unit: 0.12
    unit: oz
    motor_pin: 18
    flowmeter_pin: 25
    button_pin: 23
    pulses_per_unit: 5.2

  - id: detergent_laundry
    name: Laundry Detergent
    description: Concentrated laundry detergent
    price_per_unit: 0.20
    unit: oz
    motor_pin: 19
    flowmeter_pin: 26
    button_pin: 22
    pulses_per_unit: 5.6
```

**Recommendation:** Use JSON for simplicity (no new dependencies required)

---

### Configuration in config/__init__.py

Add new config values:
```python
# Product configuration
PRODUCTS_CONFIG_PATH = '/Users/travops/soap/ePort/config/products.json'

# Transaction settings
MAX_ITEMS_PER_TRANSACTION = 10  # Prevent abuse
PRODUCT_SWITCH_DELAY = 0.5  # Delay when switching between products (seconds)
```

---

## User Flow

### Multi-Product Transaction Flow

```
1. Customer arrives at machine
   ↓
2. Swipe card → Authorization for $20.00
   ↓
3. Authorization approved → Enable product buttons
   ↓
4. Customer presses "Hand Soap" button
   ↓
5. While holding button: dispense hand soap
   ↓
6. Customer releases button → Stop dispensing
   ↓
7. Display shows: "Hand Soap: 2.5 oz - $0.38"
   ↓
8. Customer presses "Dish Soap" button
   ↓
9. While holding button: dispense dish soap
   ↓
10. Customer releases button → Stop dispensing
    ↓
11. Display shows:
    "Hand Soap: 2.5 oz - $0.38
     Dish Soap: 3.2 oz - $0.38
     Total: $0.76"
    ↓
12. Customer presses "Done" button
    ↓
13. Transaction complete → Charge card $0.76
    ↓
14. Display: "Thank you! Machine ready for next customer"
```

---

## UI/Display Updates

### During Dispensing
```
═══════════════════════════════════
    VENDING MACHINE
═══════════════════════════════════
Select products and press DONE when
finished.

CURRENT TRANSACTION:
-----------------------------------
Hand Soap:        2.50 oz   $0.38
Dish Soap:        3.20 oz   $0.38
-----------------------------------
                  Total:    $0.76

Press product button to dispense.
Hold button to continue dispensing.
═══════════════════════════════════
```

### Transaction Complete
```
═══════════════════════════════════
    TRANSACTION COMPLETE
═══════════════════════════════════
ITEMS PURCHASED:
-----------------------------------
Hand Soap:        2.50 oz   $0.38
Dish Soap:        3.20 oz   $0.38
-----------------------------------
                  TOTAL:    $0.76

CHARGED TO CARD: $0.76

Thank you for your purchase!
═══════════════════════════════════
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] Create Product class
- [x] Create ProductManager class
- [x] Create TransactionTracker class
- [x] Add products.json config file
- [x] Write unit tests for new classes (25 tests, all passing)

**Status:** Complete - All core classes implemented and tested

### Phase 2: Integration ✅ COMPLETE
- [x] Modify MachineController to support product switching
- [x] Update main.py to use ProductManager
- [x] Implement transaction tracking in dispensing flow
- [x] Add multi-product support to transaction result
- [x] Add timeout protection (inactivity & max session)
- [x] Add customer warnings before timeout
- [x] Implement product button detection logic

**Status:** Complete - Full multi-product flow operational

**Additional Features Implemented:**
- Inactivity timeout (60 seconds) with warning at 45 seconds
- Max session timeout (5 minutes)
- Auto-complete on timeout (charge for dispensed products)
- Empty transaction handling (cancel if nothing dispensed)
- Product switch delay enforcement (0.5 seconds)
- Itemized transaction summaries
- Real-time product switching with flowmeter reconfiguration

### Phase 3: Testing & Refinement 🚧 IN PROGRESS
- [x] Add validation for max items per transaction
- [x] Test edge cases (no product dispensed, switching rapidly, etc.)
- [ ] Test with multiple products on hardware
- [ ] Refine product switching delays based on hardware testing
- [ ] Performance testing under load

**Status:** Software complete, hardware testing pending

### Phase 4: Documentation & Deployment 🚧 IN PROGRESS
- [x] Create example products.json configurations
- [x] Create comprehensive README.md
- [ ] Update SETUP.md with product configuration instructions
- [ ] Update ARCHITECTURE.md with new classes
- [ ] Deploy to production machine

**Status:** Documentation in progress

---

## Edge Cases & Error Handling

### Edge Case 1: Customer Doesn't Dispense Anything
**Scenario:** Customer authorizes card but presses "Done" without dispensing  
**Behavior:** Cancel transaction, don't charge card, show "No products dispensed"

### Edge Case 2: Customer Exceeds Authorization
**Scenario:** Customer dispenses $22.00 worth of products (auth was $20.00)  
**Behavior:** Stop allowing dispensing at $20.00, charge full $20.00, show warning

### Edge Case 3: Invalid Product Configuration
**Scenario:** products.json has duplicate button pins or missing required fields  
**Behavior:** Fail to start, log clear error message, don't accept payments

### Edge Case 4: Product Motor/Flowmeter Failure
**Scenario:** Motor doesn't respond or flowmeter doesn't send pulses  
**Behavior:** Cancel transaction, log error, show "Hardware error - please contact staff"

### Edge Case 5: Rapid Product Switching
**Scenario:** Customer rapidly presses different product buttons  
**Behavior:** Ignore button presses during PRODUCT_SWITCH_DELAY period

### Edge Case 6: Done Button Pressed During Dispensing
**Scenario:** Customer presses "Done" while holding product button  
**Behavior:** Stop motor immediately, complete transaction with current total

### Edge Case 7: Customer Walks Away (Inactivity Timeout) ✅ IMPLEMENTED
**Scenario:** Customer authorizes card, dispenses some product, then walks away without pressing "Done"  
**Behavior:**
- At 45 seconds: Display warning "⚠️ WARNING: 15 seconds until auto-complete"
- At 60 seconds: Auto-complete transaction, charge for what was dispensed
- If nothing dispensed: Cancel transaction, no charge

### Edge Case 8: Customer Takes Too Long (Max Session Timeout) ✅ IMPLEMENTED
**Scenario:** Customer stays at machine for extended period (> 5 minutes)  
**Behavior:** Force complete transaction at 5 minutes, charge for all dispensed products

### Edge Case 9: Rapid Product Switching ✅ IMPLEMENTED
**Scenario:** Customer rapidly presses different product buttons  
**Behavior:** Enforce 0.5 second delay between switches, ignore presses during delay period

---

## Data Structures

### Transaction Item
```python
{
    "product_id": "soap_hand",
    "product_name": "Hand Soap",
    "quantity": 2.5,
    "unit": "oz",
    "price": 0.38
}
```

### Transaction Summary
```python
{
    "items": [
        {"product_id": "soap_hand", "quantity": 2.5, "unit": "oz", "price": 0.38},
        {"product_id": "soap_dish", "quantity": 3.2, "unit": "oz", "price": 0.38}
    ],
    "total": 0.76,
    "timestamp": "2026-01-22T14:30:00Z"
}
```

---

## Testing Strategy

### Unit Tests
- Product class initialization and validation
- ProductManager loading and lookup
- TransactionTracker add/calculate/reset operations
- Product configuration parsing and validation

### Integration Tests
- Multi-product dispensing flow
- Product switching during transaction
- Transaction total calculation
- Payment protocol with itemized transaction

### Hardware Tests (Manual)
- Dispense multiple products in one transaction
- Switch between products rapidly
- Test all product buttons
- Verify flowmeter calibration per product

---

## Security & Safety

### Safety Limits
- `MAX_ITEMS_PER_TRANSACTION = 10` - Prevent transaction abuse
- `MAX_TRANSACTION_PRICE` (existing) - Already limits total price
- Product config validation prevents invalid GPIO assignments

### Input Validation
- Validate products.json schema on load
- Check for duplicate GPIO pins
- Verify all required fields present
- Ensure positive prices and calibration values

---

## Migration Strategy

### Backward Compatibility
**Current single-product setup should continue working:**

**Option A: Auto-migrate existing config**
- If products.json doesn't exist, create default from existing config
- Use current MOTOR_PIN, FLOWMETER_PIN, etc. as default product

**Option B: Require explicit migration**
- Document how to create products.json from existing config
- Machine won't start without products.json (forces upgrade)

**Recommendation:** Option A for smoother transition

---

## Open Questions

### Q1: Product Configuration Format
**Question:** JSON or YAML for products config?  
**Options:**
- JSON: No dependencies, standard Python library
- YAML: More readable, requires PyYAML dependency

**Recommendation:** JSON (no new dependencies)

---

### Q2: Product Selection UX
**Question:** How does customer know which button is which product?  
**Options:**
- Physical labels on buttons
- Display shows product names and button positions
- LED indicators next to each button

**Recommendation:** Physical labels + display showing active product

---

### Q3: Transaction Display
**Question:** Show running total during dispensing or only at end?  
**Options:**
- Running total: Customer sees price updating in real-time
- End only: Simpler display, summary at end

**Recommendation:** Running total for transparency

---

### Q4: Done Button Behavior
**Question:** Keep one "Done" button or add done button per product?  
**Options:**
- Single done button: Simpler hardware, ends entire transaction
- Per-product done: More complex, allows "done with this product"

**Recommendation:** Single done button (simpler, current behavior)

---

### Q5: Product Switch Confirmation
**Question:** Should machine confirm when customer switches products?  
**Options:**
- No confirmation: Seamless switching
- Brief confirmation: Display shows "Now dispensing: [Product]"

**Recommendation:** Brief confirmation for clarity

---

## Success Metrics

### Functional Metrics
- ✅ 3+ products configured and operational
- ✅ Multi-product transaction completes successfully
- ✅ Total price calculated correctly
- ✅ All products tracked individually

### Performance Metrics
- ⏱️ Product switching delay < 1 second
- ⏱️ Transaction completion time < 5 minutes
- ⏱️ Config load time < 1 second

### Quality Metrics
- 🧪 100% unit test coverage for new classes
- 🧪 All integration tests passing
- 🐛 Zero critical bugs in production

---

## Future Enhancements

### Phase 2 Features (Future)
- [ ] Product inventory tracking
- [ ] Low inventory alerts
- [ ] Product usage analytics
- [ ] Dynamic pricing (discounts, bulk rates)
- [ ] Product bundles/combos
- [ ] Customer loyalty tracking

---

## Appendix

### Example products.json for Single-Product Migration
```json
{
  "products": [
    {
      "id": "soap_hand",
      "name": "Hand Soap",
      "description": "Gentle hand wash soap",
      "price_per_unit": 0.15,
      "unit": "oz",
      "motor_pin": 17,
      "flowmeter_pin": 24,
      "button_pin": 4,
      "pulses_per_unit": 5.4
    }
  ]
}
```

This maintains current single-product behavior while enabling multi-product support.

---

**Document Status:** Ready for Review  
**Next Steps:** Review PRD → Approve → Begin Phase 1 Implementation
