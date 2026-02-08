# 🚀 Quick Installation Guide

**For Non-Technical Users - One Command Setup**

## What This Does

This script will **automatically** configure your Raspberry Pi vending machine with:
- ✅ Customer display in full-screen kiosk mode (no browser UI visible)
- ✅ Auto-start on boot
- ✅ All dependencies installed
- ✅ Everything tested and ready to use

**No technical knowledge required!**

---

## Installation Steps

### Step 1: Connect to Your Raspberry Pi

1. **Plug in:** keyboard, mouse, HDMI monitor, power
2. **Wait** for Raspberry Pi to boot to desktop
3. **Open terminal** (black window icon in top toolbar)

### Step 2: Download the Software

In the terminal, type these commands:

```bash
cd ~
git clone https://github.com/YOUR-USERNAME/soap.git
cd soap
```

*(Replace `YOUR-USERNAME` with your actual GitHub username)*

### Step 3: Run the Automatic Setup

```bash
cd ePort/scripts
chmod +x setup.sh
./setup.sh
```

**That's it!** The script will:
- Install everything automatically
- Configure kiosk mode (full-screen, no browser UI)
- Set up auto-start
- Test the system

**Time:** About 5-10 minutes

### Step 4: Reboot

When the script finishes, type:

```bash
sudo reboot
```

---

## ✅ After Reboot - What You'll See

The Raspberry Pi will:
1. **Auto-login** to desktop
2. **Automatically launch** the customer display in **full-screen mode**
3. **Show** "REFILL YOUR SOAP HERE - SWIPE CARD TO BEGIN"
4. **No browser UI** - looks like a professional kiosk!

**The system is ready for customers!**

---

## 🎉 You're Done!

Your vending machine is now:
- ✅ Fully configured
- ✅ Running in kiosk mode (no browser UI visible to customers)
- ✅ Starting automatically on boot
- ✅ Ready for credit card transactions

---

## 🛠️ Useful Commands (If Needed)

### View Live Logs
```bash
sudo journalctl -u vending-machine -f
```

### Check If Service Is Running
```bash
sudo systemctl status vending-machine
```

### Restart the Service
```bash
sudo systemctl restart vending-machine
```

### Exit Kiosk Mode (For Testing Only)
Press `Alt+F4`

---

## 🆘 Troubleshooting

### Problem: I see a browser address bar
**Solution:** The kiosk mode isn't configured. Run the setup script again:
```bash
cd ~/soap/ePort/scripts
./setup.sh
```

### Problem: Display shows "Can't reach this page"
**Solution:** The vending machine service isn't running. Check status:
```bash
sudo systemctl status vending-machine
```

If stopped, start it:
```bash
sudo systemctl start vending-machine
```

### Problem: Black screen after reboot
**Solution:** Check if the service is running:
```bash
sudo systemctl status vending-machine
```

View logs to see what happened:
```bash
sudo journalctl -u vending-machine -f
```

### Problem: Mouse cursor is visible
**Solution:** The `unclutter` package isn't working. Run setup again:
```bash
cd ~/soap/ePort/scripts
./setup.sh
```

---

## 📱 Need Help?

Contact your system administrator with:
1. The **error message** you see
2. **Output** from: `sudo journalctl -u vending-machine -n 50`

---

## 🔧 Advanced: Manual Configuration (Optional)

If you need to customize settings:

### Change Product Prices
```bash
nano ~/soap/ePort/config/products.json
```

### Change Display Timeouts
```bash
nano ~/soap/ePort/config/__init__.py
```

After any changes, restart the service:
```bash
sudo systemctl restart vending-machine
```

---

**Last Updated:** February 2026
