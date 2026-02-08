# 🚀 Deployment Guide - Raspberry Pi

**For updating vending machines with the latest code**

---

## 📋 One-Time Setup (Per Raspberry Pi)

### Step 1: Install Git (If Not Already Installed)

```bash
sudo apt update
sudo apt install -y git
```

### Step 2: Configure Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Set Up SSH Key for GitHub

#### Generate SSH Key:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```

Press **Enter** three times (default location, no passphrase for automated systems)

#### Copy the Public Key:
```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519`)

#### Add to GitHub:
1. Go to GitHub.com → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste the key
4. Click "Add SSH key"

#### Test SSH Connection:
```bash
ssh -T git@github.com
```

You should see: `Hi USERNAME! You've successfully authenticated...`

---

## 🎯 Initial Installation (First Time on New Pi)

### Option 1: Clone the Repository

```bash
cd ~
git clone git@github.com:Travbz/soap.git
cd soap
```

### Option 2: Run Automated Setup

```bash
cd ~/soap/ePort/scripts
./setup.sh
```

**OR** just run the main program (auto-detects and runs setup):

```bash
cd ~/soap
python3 -m ePort.main
```

### Reboot:
```bash
sudo reboot
```

**Done!** The system will auto-start in kiosk mode after reboot.

---

## 🔄 Updating to Latest Code (Already Deployed)

When you push new code to GitHub, employees can update any Raspberry Pi:

### Method 1: Quick Update (Recommended)

```bash
# Stop the service
sudo systemctl stop vending-machine

# Go to project directory
cd ~/soap

# Pull latest code
git pull origin main

# Restart the service
sudo systemctl start vending-machine
```

**Done!** New code is running.

### Method 2: Update with Reboot (More Thorough)

```bash
cd ~/soap
git pull origin main
sudo reboot
```

### Method 3: Update Specific Branch

If testing a feature branch:

```bash
cd ~/soap
git fetch origin
git checkout fix/simplify-display-logic
git pull origin fix/simplify-display-logic
sudo systemctl restart vending-machine
```

---

## 🔍 Checking Current Version

### See What Version Is Running:

```bash
cd ~/soap
git log -1 --oneline
```

Shows the latest commit currently deployed.

### See What Branch Is Active:

```bash
cd ~/soap
git branch --show-current
```

### Check for Available Updates:

```bash
cd ~/soap
git fetch origin
git status
```

If behind, you'll see: `Your branch is behind 'origin/main' by X commits`

---

## 🛠️ Troubleshooting Updates

### Problem: "Changes would be overwritten"

**Solution:** Stash local changes first:
```bash
cd ~/soap
git stash
git pull origin main
sudo systemctl restart vending-machine
```

### Problem: "Permission denied (publickey)"

**Solution:** SSH key not set up. Redo Step 3 above.

### Problem: Service won't start after update

**Solution:** Check logs:
```bash
sudo journalctl -u vending-machine -n 50
```

Look for Python errors, then fix and restart:
```bash
sudo systemctl restart vending-machine
```

### Problem: Want to undo update

**Solution:** Revert to previous version:
```bash
cd ~/soap
git log --oneline -10   # See last 10 commits
git checkout <commit-hash>   # Pick a previous commit
sudo systemctl restart vending-machine
```

---

## 📊 Monitoring After Update

### View Live Logs:
```bash
sudo journalctl -u vending-machine -f
```

### Check Service Status:
```bash
sudo systemctl status vending-machine
```

### Test Display Manually:
```bash
# Stop service temporarily
sudo systemctl stop vending-machine

# Run manually to see output
cd ~/soap
python3 -m ePort.main

# Press Ctrl+C to stop
# Restart service
sudo systemctl start vending-machine
```

---

## 🎨 Customizing Configuration (Without Git Conflicts)

If you need to customize settings per machine (prices, GPIO pins, etc.), use **local config overrides**:

### Option 1: Modify products.json (Local Only)

```bash
cd ~/soap/ePort/config
cp products.json products.local.json
nano products.local.json
```

Then update code to load `products.local.json` if it exists (falls back to `products.json`).

### Option 2: Environment Variables

Set machine-specific values in the systemd service:

```bash
sudo nano /etc/systemd/system/vending-machine.service
```

Add under `[Service]`:
```ini
Environment="PRODUCT_PRICE_OVERRIDE=0.20"
Environment="MACHINE_ID=vending-001"
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart vending-machine
```

---

## 🔐 Security Best Practices

### Use Read-Only SSH Keys Per Location

For each vending machine location, create a separate **read-only** deploy key:

1. Generate key on Pi:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/id_soap_readonly -C "location-001"
   ```

2. Add as **Deploy Key** on GitHub (read-only)
   - Settings → Deploy keys → Add
   - Paste public key
   - ✅ **Do NOT** check "Allow write access"

3. Configure Git to use this key:
   ```bash
   git config core.sshCommand "ssh -i ~/.ssh/id_soap_readonly"
   ```

Now that Pi can **pull** updates but **cannot push** changes back.

---

## 📱 Remote Update Strategy (Multiple Machines)

### For Managing Many Machines:

1. **Update GitHub** with new code (from your dev machine)
2. **SSH into each Pi** and run:
   ```bash
   cd ~/soap && git pull origin main && sudo systemctl restart vending-machine
   ```

### Or Create Update Script:

**`update-all.sh`** on your dev machine:
```bash
#!/bin/bash
# List of Pi IP addresses
MACHINES=(
    "pi@192.168.1.101"
    "pi@192.168.1.102"
    "pi@192.168.1.103"
)

for machine in "${MACHINES[@]}"; do
    echo "Updating $machine..."
    ssh $machine "cd ~/soap && git pull origin main && sudo systemctl restart vending-machine"
done

echo "All machines updated!"
```

Make executable:
```bash
chmod +x update-all.sh
```

Run to update all machines:
```bash
./update-all.sh
```

---

## 🎯 Quick Reference Commands

| Task | Command |
|------|---------|
| **Pull latest code** | `cd ~/soap && git pull origin main` |
| **Restart service** | `sudo systemctl restart vending-machine` |
| **View logs** | `sudo journalctl -u vending-machine -f` |
| **Check status** | `sudo systemctl status vending-machine` |
| **See current version** | `cd ~/soap && git log -1 --oneline` |
| **Check for updates** | `cd ~/soap && git fetch && git status` |
| **Reboot** | `sudo reboot` |

---

## ✅ Deployment Checklist

Before updating production machines:

- [ ] Tested on dev/staging Pi
- [ ] All tests passing (`python3 -m ePort.tests.test_payment`)
- [ ] Code pushed to GitHub
- [ ] Created release/tag (optional)
- [ ] Backed up current config files (if customized)
- [ ] Scheduled update during low-traffic time
- [ ] Have rollback plan ready

---

**Last Updated:** February 2026
