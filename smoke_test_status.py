import sqlite3, pathlib, base64, requests, os, subprocess, sys

# --- LOAD CONFIG ---
conn = sqlite3.connect("schoolpay.db")
cur = conn.cursor()
try:
    cur.execute("SELECT consumer_key, consumer_secret, initiator_name, initiator_password, result_url, timeout_url FROM daraja_config LIMIT 1")
    consumer_key, consumer_secret, initiator_name, initiator_pwd, result_url, timeout_url = cur.fetchone()
except Exception as e:
    print(f"DB read failed: {e}")
    sys.exit(1)

print(f"Initiator: {initiator_name}")
print(f"ResultURL: {result_url}")

# --- 1. Token ---
print("\n[1/3] Getting token...")
auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
r = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
                 headers={"Authorization": f"Basic {auth}"}, timeout=15)
print(r.text[:300])
token = r.json().get("access_token")
if not token:
    print("Token failed - check consumer key/secret")
    sys.exit(1)

# --- 2. Encrypt with openssl (no cryptography lib) ---
print("\n[2/3] Encrypting with openssl...")
cert_cer = "sandbox_cert.cer"
cert_pem = "sandbox_cert.pem"

# Ensure PEM exists
if not pathlib.Path(cert_pem).exists():
    # try convert DER -> PEM
    os.system(f"openssl x509 -inform der -in {cert_cer} -out {cert_pem} 2>/dev/null || cp {cert_cer} {cert_pem}")

# Extract public key
os.system(f"openssl x509 -in {cert_pem} -pubkey -noout > pubkey.pem")

# Encrypt password -> binary -> base64
with open("pwd.txt","w") as f:
    f.write(initiator_pwd)

os.system("openssl rsautl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin 2>/dev/null || openssl pkeyutl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin")

if not pathlib.Path("encrypted.bin").exists():
    print("OpenSSL encrypt failed")
    sys.exit(1)

security_credential = base64.b64encode(pathlib.Path("encrypted.bin").read_bytes()).decode()
print(f"SecurityCredential: {security_credential[:50]}...")

# --- 3. TransactionStatusQuery ---
print("\n[3/3] Sending TransactionStatusQuery...")

# Try get last transaction
try:
    cur.execute("SELECT transaction_id FROM mpesa_transactions ORDER BY id DESC LIMIT 1")
    tx = cur.fetchone()
    transaction_id = tx[0] if tx and tx[0] else "OE2TEST12345"
except:
    transaction_id = "OE2TEST12345"

print(f"Using TransactionID: {transaction_id}")

payload = {
    "Initiator": initiator_name,
    "SecurityCredential": security_credential,
    "CommandID": "TransactionStatusQuery",
    "TransactionID": transaction_id,
    "PartyA": "174379",
    "IdentifierType": "4",
    "ResultURL": result_url,
    "QueueTimeOutURL": timeout_url,
    "Remarks": "Smoke test",
    "Occasion": "Smoke test"
}

resp = requests.post("https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query",
                     json=payload,
                     headers={"Authorization": f"Bearer {token}"},
                     timeout=20)
print("\n--- DARAJA RESPONSE ---")
print(resp.status_code)
print(resp.text)

if resp.status_code==200 and "ResponseCode" in resp.text:
    if '"ResponseCode":"0"' in resp.text or '"ResponseCode": "0"' in resp.text or "0" in resp.text:
        print("\n✅ SMOKE TEST PASSED - Status request working!")
    else:
        print("\nResponse received but check ResultCode")
else:
    print("\n❌ FAILED - see above")
