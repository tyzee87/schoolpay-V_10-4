#!/data/data/com.termux/files/usr/bin/bash
echo "=== SchoolPay V10.4 HYBRID AUTO + CHROME ==="
pkill -f cloudflared 2>/dev/null
rm -f tunnel.log flask.log
pkg install termux-tools -y > /dev/null 2>&1

RENDER_KEY=$(cat ~/.render_api_key 2>/dev/null)
SERVICE_ID=$(cat ~/.render_service_id 2>/dev/null)

# 1. START CLOUDFLARE
echo "[1/5] Starting Cloudflare..."
cloudflared tunnel --url http://127.0.0.1:5000 --no-autoupdate > tunnel.log 2>&1 &
sleep 7

for i in {1..25}; do
  CF_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -n1)
  [ -n "$CF_URL" ] && break
  echo "Waiting Cloudflare... $i"
  sleep 2
done

if [ -z "$CF_URL" ]; then cat tunnel.log; exit 1; fi
echo "✅ LIVE: $CF_URL"
echo "$CF_URL/mpesa/callback" > live_forward_url.txt
FORWARD_URL="$CF_URL/mpesa/callback"

# 2. AUTO-UPDATE RENDER
echo "[2/5] Updating Render..."
curl -s -X PUT "https://api.render.com/v1/services/$SERVICE_ID/env-vars/TERMUX_FORWARD_URL" \
  -H "Authorization: Bearer $RENDER_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"key\":\"TERMUX_FORWARD_URL\",\"value\":\"$FORWARD_URL\"}" > /tmp/r.json
curl -s -X POST "https://api.render.com/v1/services/$SERVICE_ID/deploys" -H "Authorization: Bearer $RENDER_KEY" -d '{}' > /dev/null
echo "✅ Render updated"

# 3. START SCHOOLPAY IN BACKGROUND
echo "[3/5] Starting SchoolPay..."
export MPESA_CALLBACK_URL="https://schoolpay-v-10-4.onrender.com/mpesa/callback"
export TERMUX_FORWARD_URL="$FORWARD_URL"
export MPESA_CALLBACK_TOKEN="SchoolPay2026Secret_9d28"
export CALLBACK_TOKEN="SchoolPay2026Secret_9d28"
python3 app.py > flask.log 2>&1 &
sleep 4
cat flask.log | tail -n 5

# 4. AUTO START CHROME - TERMUX LIVE + LOCAL
echo "[4/5] Opening Chrome..."
# Open LIVE link
termux-open-url "$CF_URL/login" 2>/dev/null || am start --user 0 -a android.intent.action.VIEW -d "$CF_URL/login" > /dev/null 2>&1
sleep 2
# Also open local as backup
termux-open-url "http://127.0.0.1:5000/login" 2>/dev/null || true

echo ""
echo "=============================="
echo "SDK (Render): https://schoolpay-v-10-4.onrender.com/mpesa/callback"
echo "LIVE (Cloudflare): $CF_URL/login"
echo "Local: http://127.0.0.1:5000/login"
echo "Login: admin / admin123"
echo "=============================="
echo "[5/5] Logs: tail -f flask.log"
echo "Chrome should open automatically!"
wait
