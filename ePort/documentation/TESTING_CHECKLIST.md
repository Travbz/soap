# Testing Checklist for fix/simplify-display-logic Branch

## Expected Behavior

### Test 1: Single Product
1. Swipe card → Approved
2. Press and hold Hand Soap button
3. **Expected:** Counter shows 0.0oz → increases in real-time
4. **Expected:** Product tile is GREEN (active)
5. Release button at 5.0oz
6. **Expected:** Product tile turns BLUE, shows 5.0oz
7. **Expected:** Grand total shows $0.75 (15¢/oz × 5oz)

### Test 2: Multiple Products (Different)
1. Swipe card → Approved
2. Dispense Hand Soap: 5.0oz
3. **Expected:** Hand Soap shows 5.0oz BLUE, Total: $0.75
4. Press Dish Soap button
5. **Expected:** Dish Soap counter starts at 0.0oz (not 5.0oz!)
6. Dispense Dish Soap: 3.0oz
7. **Expected:** 
   - Hand Soap: 5.0oz BLUE (stays visible)
   - Dish Soap: 3.0oz GREEN → BLUE on release
   - Total: $1.11
8. Press Laundry Gel button
9. Dispense Laundry Gel: 4.0oz
10. **Expected:**
    - Hand Soap: 5.0oz BLUE
    - Dish Soap: 3.0oz BLUE
    - Laundry Gel: 4.0oz GREEN → BLUE
    - Total: $1.51

### Test 3: Same Product Multiple Times
1. Swipe card → Approved
2. Dispense Hand Soap: 5.0oz
3. **Expected:** Hand Soap shows 5.0oz BLUE
4. Press Dish Soap button, dispense 3.0oz
5. **Expected:** Hand Soap still shows 5.0oz, Dish Soap shows 3.0oz
6. Press Hand Soap button AGAIN
7. **Expected:** Hand Soap counter starts at 5.0oz (accumulated!)
8. Dispense 2.0oz more Hand Soap
9. **Expected:** Hand Soap shows 5.0oz → 5.1oz → ... → 7.0oz
10. Release button
11. **Expected:**
    - Hand Soap: 7.0oz BLUE (5 + 2 accumulated)
    - Dish Soap: 3.0oz BLUE
    - Total: $1.41

### Test 4: Waiting Screen
1. Start dispensing any product
2. Release button
3. Wait 3 seconds without pressing anything
4. **Expected:** Screen changes to "PRESS DONE BUTTON"
5. **Expected:** Product totals remain visible on product bar
6. Press any product button
7. **Expected:** Returns to dispensing screen

### Test 5: Receipt Display
1. Complete a transaction (dispense products, press DONE)
2. **Expected:** Receipt displays with:
   - All products with accumulated totals
   - Correct prices per product
   - Correct grand total
3. **Expected:** Receipt stays visible for 10 seconds
4. **Expected:** After 10 seconds, returns to idle (swipe card) screen

## Known Issues to Watch For

❌ **Bug:** Product 2 counter starts at Product 1's amount
- This means flowmeter callback is getting wrong previous value

❌ **Bug:** Product tile stays GREEN after button release
- This means button_was_pressed flag isn't working

❌ **Bug:** Product tiles flicker GREEN → BLUE → GREEN
- This means we're updating display too many times

❌ **Bug:** Receipt flashes briefly
- This means state transition is happening before 10s timeout

## If Bugs Occur

If any of the above bugs occur, revert to commit BEFORE this branch and we'll start fresh with a simpler approach.

**Last known good commit:** (check git log)

**Revert command:**
```bash
git checkout main
git reset --hard <commit-hash>
```
