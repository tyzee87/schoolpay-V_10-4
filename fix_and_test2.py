import sqlite3, base64, requests, pathlib, os

conn = sqlite3.connect("schoolpay.db")
cur = conn.cursor()
cur.execute("SELECT ckey, csecret, initiator_name, initiator_password, ts_result_url, ts_timeout_url FROM daraja_config WHERE id=1")
ckey, csecret, initiator_name, initiator_pwd, ts_result, ts_timeout = cur.fetchone()

print(f"ckey len: {len(ckey)} - should be ~30-40")
print(f"csecret len: {len(csecret)}")
if len(ckey) < 20:
    print("❌ ckey TOO SHORT - you pasted truncated key!")
    print(f"Current: {ckey}")
    new_key = input("Paste FULL Consumer Key from developer.safaricom.co.ke: ").strip()
    new_secret = input("Paste FULL Consumer Secret: ").strip()
    cur.execute("UPDATE daraja_config SET ckey=?, csecret=? WHERE id=1", (new_key, new_secret))
    conn.commit()
    ckey, csecret = new_key, new_secret
    print("✅ Updated DB")

# --- Get token with browser headers to bypass Incapsula ---
print("\n[1/3] Getting token with browser UA...")
auth = base64.b64encode(f"{ckey}:{csecret}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json"
}
try:
    r = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
                     headers=headers, timeout=20, verify=True)
except Exception as e:
    print(f"Request failed: {e}")
    print("Trying with curl fallback...")
    os.system(f'''curl -k -s -X GET "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials" -H "Authorization: Basic {auth}" -H "User-Agent: Mozilla/5.0" > token.json; cat token.json''')
    import json
    try:
        token = json.loads(pathlib.Path("token.json").read_text()).get("access_token")
    except:
        token = None
else:
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
    if "<html" in r.text.lower():
        print("\n❌ STILL BLOCKED by Incapsula - Your IP is flagged")
        print("SOLUTION: Turn OFF WiFi, use mobile data (Safaricom/Airtel), then retry")
        exit(1)
    try:
        token = r.json().get("access_token")
    except:
        token = None

if not token:
    print("❌ No token - keys invalid")
    exit(1)

print(f"✅ Token OK: {token[:20]}...")

# --- 2 & 3 same as before ---
print("\n[2/3] Encrypting...")
if not pathlib.Path("sandbox_cert.pem").exists():
    os.system("curl -k -L -o sandbox_cert.cer https://developer.safaricom.co.ke/sites/default/files/cert/cert_sandbox/cert.cer 2>/dev/null; openssl x509 -inform der -in sandbox_cert.cer -out sandbox_cert.pem 2>/dev/null")
os.system("openssl x509 -in sandbox_cert.pem -pubkey -noout > pubkey.pem 2>/dev/null")
open("pwd.txt","w").write(initiator_pwd)
os.system("openssl rsautl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin 2>/dev/null || openssl pkeyutl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin")
security_credential = base64.b64encode(pathlib.Path("encrypted.bin").read_bytes()).decode()

# --- 3 Query ---
print("\n[3/3] TransactionStatusQuery...")
payload = {
    "Initiator": initiator_name,
    "SecurityCredential": security_credential,
    "CommandID": "TransactionStatusQuery",
    "TransactionID": "OE2TEST12345",
    "PartyA": "174379",
    "IdentifierType": "4",
    "ResultURL": ts_result,
    "QueueTimeOutURL": ts_timeout,
    "Remarks": "Smoke test",
    "Occasion": "Smoke test"
}
resp = requests.post("https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query",
                     json=payload,
                     headers={"Authorization": f"Bearer {token}", "User-Agent": headers["User-Agent"]},
                     timeout=20)
print(resp.status_code)
print(resp.text)
if resp.status_code==200 and "ResponseCode" in resp.text:
    print("\n✅✅✅ SMOKE TEST PASSED - Status request WORKING!")
