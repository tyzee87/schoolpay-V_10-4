#!/data/data/com.termux/files/usr/bin/bash
cd ~/SchoolPay_V10
pkill -f app.py; pkill -f cloudflared; rm -f tunnel.log

# EXPORT THE TOKEN - THIS FIXES YOUR ERROR
export MPESA_CALLBACK_TOKEN=SchoolPay2026SecureToken123
export DARAJA_ENV=sandbox
# Load .env if exists
[ -f .env ] && export $(cat .env | xargs)

# Auto-update to Render for callbacks
RENDER="https://schoolpay-v-10-4.onrender.com"
sqlite3 schoolpay.db "UPDATE daraja_config SET result_url='$RENDER/mpesa/transactionstatus/result', timeout_url='$RENDER/mpesa/transactionstatus/timeout';" 2>/dev/null

# Patch app.py callbacks to Render
python3 -c "
import pathlib,re
p=pathlib.Path('app.py').read_text()
R='https://schoolpay-v-10-4.onrender.com'
p=re.sub(r'\"CallBackURL\"\s*:\s*\"[^\"]+\"', f'\"CallBackURL\": \"{R}/mpesa/callback?token=SchoolPay2026SecureToken123\"', p)
pathlib.Path('app.py').write_text(p)
"

echo "Token set: $MPESA_CALLBACK_TOKEN"
echo "Starting tunnel..."
nohup cloudflared tunnel --url http://127.0.0.1:5000 > tunnel.log 2>&1 &
sleep 10
URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -n1)
echo "========================================"
echo "LINK: $URL/pay"
echo "TOKEN: $MPESA_CALLBACK_TOKEN"
echo "========================================"
am start -a android.intent.action.VIEW -d "$URL/pay" > /dev/null 2>&1 &
python3 app.py
