# Display Testing & Production Readiness TODOs

## Testing Required

### 1. Machine Error Display Testing
- [ ] Test error screen triggers correctly on hardware failure
- [ ] Test error screen triggers correctly on payment protocol error
- [ ] Test error screen triggers correctly on timeout errors
- [ ] Verify error screen shows appropriate message to customer
- [ ] Test that error screen auto-recovers after ERROR_DISPLAY_TIMEOUT (10s)

**How to test error display manually:**
```bash
cd ~/soap
python3 -m ePort.tests.test_display
# Navigate to error state using arrow keys
```

**Test in production scenario:**
- Disconnect ePort device and attempt transaction
- Trigger GPIO error (disconnect hardware)
- Force timeout condition
- Check that customer sees error screen, not raw Python traceback

---

## Production Configuration Needed

### 2. Error Screen Contact Information
**TODO: Ask Adam what should be displayed on error screen**

Current error screen shows:
- Generic "MACHINE ERROR" message
- "Please contact staff for assistance"
- Error code (technical details)

**Questions for Adam:**
- [ ] What company name should be displayed?
- [ ] What phone number should customers call?
- [ ] Should we show email address?
- [ ] Should we show QR code for support?
- [ ] Should we display machine ID or location?
- [ ] Should we show company logo?
- [ ] What hours is support available?

**Suggested error screen content:**
```
MACHINE ERROR

We apologize for the inconvenience.
Please contact our support team:

[COMPANY NAME]
Phone: [SUPPORT PHONE]
Email: [SUPPORT EMAIL]

Machine ID: [LOCATION/ID]
Error Code: [TECHNICAL CODE]

Available: [SUPPORT HOURS]
```

**Files to update after getting info from Adam:**
1. `ePort/display/templates/index.html` - Error screen HTML
2. `ePort/display/static/styles.css` - Error screen styling
3. `ePort/config/__init__.py` - Add support contact constants:
   ```python
   # Support contact information
   SUPPORT_COMPANY_NAME = "Soap Company Name"
   SUPPORT_PHONE = "1-800-XXX-XXXX"
   SUPPORT_EMAIL = "support@company.com"
   SUPPORT_HOURS = "Mon-Fri 8am-6pm EST"
   ```
4. `ePort/src/display_server.py` - Pass support info to error screen

---

## Technician Information Needs

### 3. Information Technicians Need for Troubleshooting
**TODO: Ask Adam what diagnostic info techs need**

**Questions for Adam:**
- [ ] Should error screen show different info to technicians vs customers?
- [ ] Do techs need to see detailed error codes?
- [ ] Should there be a "tech mode" accessible via button combination?
- [ ] What diagnostic information helps techs fix issues fastest?
- [ ] Should we log errors to remote server for monitoring?
- [ ] Do techs need to see serial numbers, firmware versions, etc?

**Potential tech-facing information:**
- Detailed Python exception traceback
- Hardware status (GPIO pin states, serial connection)
- Last successful transaction info
- System uptime and restart count
- Network connectivity status
- Software version number
- Configuration checksum

**Implementation options:**
1. **Hidden tech screen**: Press specific button combination (e.g., hold Done + Product 1)
2. **Remote logging**: Send error details to monitoring server (see PRD-CentralizedLogging.md)
3. **Local log file**: Techs SSH in and read logs via `journalctl`
4. **QR code**: Customer scans QR that includes error details in URL

---

## Display Polish Items

### 4. Additional Display Testing
- [ ] Test all state transitions work correctly
- [ ] Test product bar updates in real-time during dispensing
- [ ] Test receipt displays all products correctly
- [ ] Test waiting screen appears after WAITING_SCREEN_TIMEOUT (2s)
- [ ] Test display works on different screen resolutions
- [ ] Test display readable in bright store lighting
- [ ] Test display readable from 5+ feet away (customer distance)

### 5. Branding & Customization
**TODO: Get branding assets from Adam**
- [ ] Company logo (PNG, transparent background, high-res)
- [ ] Brand colors (hex codes) for theme
- [ ] Font preferences (if any)
- [ ] Any promotional messaging for idle screen?

---

## Production Deployment Checklist

### Before deploying to customer locations:
- [ ] Test error screen thoroughly
- [ ] Add support contact information
- [ ] Configure machine ID/location identifier
- [ ] Test kiosk mode autostart
- [ ] Test auto-recovery from power loss
- [ ] Verify systemd service starts on boot
- [ ] Test with actual ePort device (not mock)
- [ ] Test with actual GPIO hardware
- [ ] Verify display visible from customer distance
- [ ] Get Adam's approval on all customer-facing text

---

## Related Documentation
- `PRD-CustomerDisplay.md` - Original display requirements
- `KIOSK_SETUP.txt` - Kiosk mode setup instructions
- `TESTING.md` - Overall testing strategy
- `PRD-CentralizedLogging.md` - Remote error logging (future)

---

**Status**: Pending input from Adam
**Priority**: High - needed before production deployment
**Owner**: Travis (waiting on Adam's feedback)
