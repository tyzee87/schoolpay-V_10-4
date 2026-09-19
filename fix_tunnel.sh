#!/bin/bash
set -e
RENDER="https://schoolpay-v-10-4.onrender.com"
echo "=== 1/3 Fixing DB URLs to $RENDER ==="
sqlite3 schoolpay.db "UPDATE daraja_config SET ts_result_url='$RENDER/mpesa/transactionstatus/result', ts_timeout_url='$RENDER/mpesa/transactionstatus/timeout', callback_url='$RENDER/mpesa/callback', result_url='$RENDER/mpesa/callback' WHERE id=1; SELECT ts_result_url, callback_url FROM daraja_config WHERE id=1;"

echo "=== 2/3 Patching app.py ==="
cp app.py app.py.bak

python3 << 'PYINNER'
import pathlib
p = pathlib.Path("app.py")
txt = p.read_text()

if "/proxy/daraja-token" in txt:
    print("Proxy routes already exist, skipping inject")
else:
    inject = '''
@app.route('/proxy/daraja-token')
def proxy_daraja_token():
    import sqlite3, base64, requests
    conn = sqlite3.connect("schoolpay.db")
    ckey, csecret = conn.execute("SELECT ckey, csecret FROM daraja_config WHERE id=1").fetchone()
    auth = __import__("base64").b64encode(f"{ckey}:{csecret}".encode()).decode()
    r = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", headers={"Authorization": f"Basic {auth}", "User-Agent": "Mozilla/5.0"}, timeout=15)
    try:
        return r.json()
    except:
        return {"raw": r.text[:500], "status": r.status_code}

@app.route('/proxy/status-query/<txid>')
def proxy_status_query(txid):
    import sqlite3, base64, requests, pathlib, os
    conn = sqlite3.connect("schoolpay.db")
    ckey, csecret, iname, ipwd, ts_res, ts_to = conn.execute("SELECT ckey, csecret, initiator_name, initiator_password, ts_result_url, ts_timeout_url FROM daraja_config WHERE id=1").fetchone()
    auth = base64.b64encode(f"{ckey}:{csecret}".encode()).decode()
    tok_r = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", headers={"Authorization": f"Basic {auth}", "User-Agent": "Mozilla/5.0"}, timeout=15)
    tok = tok_r.json().get("access_token")
    if not tok:
        return {"error": "token failed", "raw": tok_r.text[:500]}
    # encrypt
    if not pathlib.Path("sandbox_cert.pem").exists():
        # try get from DB
        try:
            pem = conn.execute("SELECT certificate_pem FROM daraja_config WHERE id=1").fetchone()[0]
            if pem and "BEGIN CERTIFICATE" in pem:
                pathlib.Path("sandbox_cert.pem").write_text(pem)
        except:
            pass
    os.system("openssl x509 -in sandbox_cert.pem -pubkey -noout > pubkey.pem 2>/dev/null; echo -n '%s' > pwd.txt; openssl pkeyutl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin 2>/dev/null || openssl rsautl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin" % ipwd)
    os.system("base64 encrypted.bin > cred.txt 2>/dev/null")
    cred = pathlib.Path("cred.txt").read_text().strip() if pathlib.Path("cred.txt").exists() else ""
    payload = {"Initiator": iname, "SecurityCredential": cred, "CommandID": "TransactionStatusQuery", "TransactionID": txid, "PartyA": "174379", "IdentifierType": "4", "ResultURL": ts_res, "QueueTimeOutURL": ts_to, "Remarks": "via Render", "Occasion": "via Render"}
    r = requests.post("https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query", json=payload, headers={"Authorization": f"Bearer {tok}", "User-Agent": "Mozilla/5.0"}, timeout=20)
    try:
        return r.json()
    except:
        return {"raw": r.text[:1000], "status": r.status_code}

''' % ()
    # inject before if __name__
    if "if __name__ ==" in txt:
        txt = txt.replace("if __name__ ==", inject + "\nif __name__ ==")
    else:
        txt = txt + "\n" + inject
    p.write_text(txt)
    print("Injected proxy routes OK")

PYINNER

echo "=== 3/3 Pushing to Render ==="
git add app.py
git commit -m "use render as tunnel - fix status urls" || echo "nothing to commit"
git push
echo ""
echo "DONE. Wait 60s for Render deploy, then test:"
echo "curl https://schoolpay-v-10-4.onrender.com/proxy/daraja-token"
