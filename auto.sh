#!/bin/bash
pkill -9 -f app.py; pkill -9 -f cloudflared; pkill -9 python
sleep 1
# fix time import if missing
grep -q "^import time" app.py || sed -i '1i import time' app.py

echo "[*] Starting SchoolPay..."
nohup python app.py > app.log 2>&1 &
sleep 3

echo "[*] Starting Cloudflare Tunnel..."
rm -f cf.log
nohup cloudflared tunnel --url http://localhost:5000 > cf.log 2>&1 &

echo "[*] Waiting for URL..."
for i in {1..20}; do
  URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" cf.log | head -n1)
  if [ ! -z "$URL" ]; then
    echo ""
    echo "=============================="
    echo " YOUR LIVE URL IS:"
    echo " $URL"
    echo "=============================="
    echo ""
    echo " STK Callback URL:"
    echo " $URL/mpesa_callback/SchoolPay2026Secret"
    echo ""
    # auto update config.env
    sed -i "s|^MPESA_CALLBACK_URL=.*|MPESA_CALLBACK_URL=$URL/mpesa_callback/SchoolPay2026Secret|" config.env
    echo "[✓] config.env updated!"
    echo ""
    echo "Open in Chrome: $URL/login"
    echo "Login: admin / admin123"
    break
  fi
  sleep 1
  echo -n "."
done

if [ -z "$URL" ]; then
  echo "Failed. Check cf.log"
  cat cf.log
fi
