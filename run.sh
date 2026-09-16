#!/data/data/com.termux/files/usr/bin/bash
cd ~/SchoolPay_V10/SchoolPay_V10
# Start Flask in background
nohup python app.py > app.log 2>&1 &
echo "App started..."
sleep 3
cat app.log | tail -5

# Tunnel loop forever - keeps same process alive
while true; do
  echo "=== Starting Tunnel... ==="
  ssh -o ServerAliveInterval=20 -o ServerAliveCountMax=2 -R 80:127.0.0.1:5000 nokey@localhost.run 2>&1 | tee tunnel.log | while read line; do
    echo "$line"
    # Auto-extract link like https://xxxx.lhr.life
    URL=$(echo "$line" | grep -o "https://[a-z0-9]*\.lhr\.life" | head -1)
    if [ ! -z "$URL" ]; then
      echo ""
      echo "========================================"
      echo "YOUR LIVE LINK: $URL/login"
      echo "========================================"
      echo ""
      # Auto-update callback
      sed -i "s|https://.*lhr.life|$URL|g" config.env
      grep CALLBACK config.env
      # Restart app with new callback
      pkill -9 -f app.py; sleep 1
      nohup python app.py > app.log 2>&1 &
      echo "App restarted with new callback: $URL/mpesa/callback"
    fi
  done
  echo "Tunnel closed, reconnecting in 3s..."
  sleep 3
done
