#!/bin/bash
# Kiosk Launcher - Waits for the vending machine display server then opens Chromium
# Called by LXDE autostart on desktop login

URL="http://localhost:5000"
MAX_WAIT=60  # Max seconds to wait for server

echo "[kiosk] Waiting for display server at $URL ..."

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" "$URL" | grep -q "200"; then
        echo "[kiosk] Server is up after ${elapsed}s - launching browser"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $MAX_WAIT ]; then
    echo "[kiosk] Server not ready after ${MAX_WAIT}s - launching browser anyway"
fi

# Launch Chromium in full-screen kiosk mode
exec chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-translate \
    --check-for-update-interval=31536000 \
    --disable-features=TranslateUI \
    "$URL"
