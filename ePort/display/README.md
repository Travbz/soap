# Customer Display System

Web-based visual display for customer guidance and real-time transaction information.

## Quick Start

```bash
# Install dependencies
pip install flask flask-socketio

# Test display (standalone)
python3 -m ePort.test_display

# Open browser
http://localhost:5000
```

## File Structure

```
display/
├── templates/
│   └── index.html          # All 7 states in one HTML file
├── static/
│   ├── styles.css          # Owner can customize colors/fonts
│   ├── app.js              # WebSocket client
│   └── images/             # Graphics (future)
└── README.md               # This file
```

## States

1. **idle** - Swipe card prompt
2. **authorizing** - Processing payment
3. **ready** - Product selection instructions
4. **dispensing** - Live counters (artist's primary screen)
5. **complete** - Receipt (artist's receipt screen)
6. **declined** - Card declined
7. **error** - Machine error

## Customization

### Change Colors

Edit `static/styles.css`:

```css
body {
    background: #000000;  /* Black background */
    color: #FFFFFF;       /* White text */
}

.warning {
    color: #FF0000;       /* Red warning */
}
```

### Change Fonts

```css
body {
    font-family: Arial, sans-serif;  /* Change to any font */
}
```

### Change Timing

Edit `ePort/config/__init__.py`:

```python
RECEIPT_DISPLAY_TIMEOUT = 10  # Seconds
```

## Production Deployment

### Install Chromium

```bash
sudo apt install chromium-browser unclutter
```

### Configure Kiosk Mode

Edit `/etc/xdg/lxsession/LXDE-pi/autostart`:

```bash
@unclutter -idle 0
@chromium-browser --kiosk --noerrdialogs http://localhost:5000
```

### Enable Auto-Login

```bash
sudo raspi-config
# Boot Options → Desktop Autologin
```

## Troubleshooting

**Display not showing:**
- Check server is running: `curl http://localhost:5000/health`
- Check browser is pointing to correct URL
- Check display enabled: `DISPLAY_ENABLED = True` in config

**Updates not real-time:**
- Check WebSocket connection in browser console
- Verify flask-socketio is installed

**Styling looks wrong:**
- Clear browser cache (Ctrl+Shift+R)
- Check CSS file loaded: view source in browser
