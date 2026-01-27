# Customer Display - Quick Start

Super simple setup for the visual display system.

## One-Line Setup

```bash
cd ~/soap/ePort
./setup_display.sh
```

That's it! The script handles everything.

## After Setup

1. Reboot: `sudo reboot`
2. Run: `python3 -m ePort.main`

Display shows automatically.

## Troubleshooting

**Display not showing:**
```bash
chromium-browser --kiosk http://localhost:5000
```

**Disable display:**
Edit `config/__init__.py`, set `DISPLAY_ENABLED = False`
