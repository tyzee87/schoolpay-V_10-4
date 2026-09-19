#!/data/data/com.termux/files/usr/bin/bash
pkill -f cloudflared; pkill -f app.py
rm -f tunnel.log flask.log
echo "Starting stable tunnel..."
while true; do
  cloudflared tunnel --url http://127.0.0.1:5000 --no-autoupdate > tunnel.log 2>&1 &
  sleep 8
  URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -n1)
  if [ -n "$URL" ]; then
    echo "✅ LIVE: $URL"
    echo "$URL/mpesa/callback" > live_forward_url.txt
    break
  fi
  pkill -f cloudflared; sleep 3
done

export MPESA_CALLBACK_URL="https://schoolpay-v-10-4.onrender.com/mpesa/callback"
export TERMUX_FORWARD_URL="$(cat live_forward_url.txt)"
export MPESA_CALLBACK_TOKEN="SchoolPay2026Secret_9d28"
export CALLBACK_TOKEN="SchoolPay2026Secret_9d28"
python3 app.py > flask.log 2>&1 &
sleep 3
termux-open-url "$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -n1)/pay" 2>/dev/null || true
echo "Chrome opened. Logs: tail -f flask.log"
tail -f flask.log
