#!/data/data/com.termux/files/usr/bin/bash
echo "=== SchoolPay V10.4 HYBRID AUTORUN ==="
pkill -f cloudflared 2>/dev/null
rm -f tunnel.log live_forward_url.txt

# 1. START CLOUDFLARE FOR TERMUX LIVE
echo "[1/3] Starting Cloudflare tunnel for Termux LIVE..."
cloudflared tunnel --url http://127.0.0.1:5000 --no-autoupdate > tunnel.log 2>&1 &
sleep 5

# 2. EXTRACT CLOUDFLARE LINK
for i in {1..20}; do
  CF_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -n1)
  if [ -n "$CF_URL" ]; then break; fi
  echo "Waiting for Cloudflare link... $i"
  sleep 2
done

if [ -z "$CF_URL" ]; then
  echo "❌ Failed to get Cloudflare URL - check tunnel.log"
  cat tunnel.log
  exit 1
fi

echo "✅ TERMUX LIVE: $CF_URL"
echo "$CF_URL/mpesa/callback" > live_forward_url.txt
echo "$CF_URL" > live_url.txt

# 3. SET HYBRID ENV - THIS IS WHAT YOU WANTED
export MPESA_CALLBACK_URL="https://schoolpay-v-10-4.onrender.com/mpesa/callback"
export TERMUX_FORWARD_URL="$CF_URL/mpesa/callback"
export MPESA_CALLBACK_TOKEN="SchoolPay2026Secret_9d28"
export CALLBACK_TOKEN="SchoolPay2026Secret_9d28"

echo ""
echo "=== HYBRID CONFIG ==="
echo "SDK Validation/Confirmation -> $MPESA_CALLBACK_URL (Render - stable)"
echo "Termux LIVE Link           -> $CF_URL"
echo "Forwarder                  -> Render will forward to $TERMUX_FORWARD_URL"
echo ""

# 4. SHOW WHAT TO UPDATE ON RENDER (only when link changes)
echo "⚠️  UPDATE THIS ON RENDER DASHBOARD -> Environment:"
echo "TERMUX_FORWARD_URL=$CF_URL/mpesa/callback"
echo ""

# 5. START APP
echo "[2/3] Starting SchoolPay..."
python3 app.py
