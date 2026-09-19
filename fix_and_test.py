import sqlite3, pathlib, base64, requests, os, subprocess

conn = sqlite3.connect("schoolpay.db")
cur = conn.cursor()

# 1. FIX ts_result_url to stable Render
RENDER = "https://schoolpay-v-10-4.onrender.com"
cur.execute(f"UPDATE daraja_config SET ts_result_url='{RENDER}/mpesa/transactionstatus/result', ts_timeout_url='{RENDER}/mpesa/transactionstatus/timeout', callback_url='{RENDER}/mpesa/callback' WHERE id=1")
conn.commit()
print(f"✅ Fixed URLs to {RENDER}")

cur.execute("SELECT ckey, csecret, initiator_name, initiator_password, certificate_pem, ts_result_url, ts_timeout_url FROM daraja_config WHERE id=1")
ckey, csecret, initiator_name, initiator_pwd, cert_pem_db, ts_result, ts_timeout = cur.fetchone()
print(f"ckey: {ckey[:6]}..., initiator: {initiator_name}, pwd len: {len(initiator_pwd)}")
print(f"ts_result_url: {ts_result}")
print(f"ts_timeout_url: {ts_timeout}")

# 2. Get token
auth = base64.b64encode(f"{ckey}:{csecret}".encode()).decode()
r = requests.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
                 headers={"Authorization": f"Basic {auth}"}, timeout=15)
print("\nToken response:", r.text[:400])
token = r.json().get("access_token")
if not token:
    print("❌ Token failed - check ckey/csecret")
    exit(1)

# 3. Ensure cert PEM file
# Use cert from DB if exists, else from file
if cert_pem_db and "BEGIN CERTIFICATE" in cert_pem_db:
    pathlib.Path("sandbox_cert.pem").write_text(cert_pem_db)
else:
    # use downloaded file
    if not pathlib.Path("sandbox_cert.pem").exists():
        os.system("curl -k -L -o sandbox_cert.cer https://developer.safaricom.co.ke/sites/default/files/cert/cert_sandbox/cert.cer 2>/dev/null; openssl x509 -inform der -in sandbox_cert.cer -out sandbox_cert.pem 2>/dev/null || cp sandbox_cert.cer sandbox_cert.pem")

os.system("openssl x509 -in sandbox_cert.pem -pubkey -noout > pubkey.pem 2>/dev/null")
open("pwd.txt","w").write(initiator_pwd)
os.system("openssl rsautl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin 2>/dev/null || openssl pkeyutl -encrypt -pubin -inkey pubkey.pem -in pwd.txt -out encrypted.bin")

security_credential = base64.b64encode(pathlib.Path("encrypted.bin").read_bytes()).decode()
print(f"\nSecurityCredential: {security_credential[:40]}...")

# 4. Smoke test TransactionStatusQuery
payload = {
    "Initiator": initiator_name,
    "SecurityCredential": security_credential,
    "CommandID": "TransactionStatusQuery",
    "TransactionID": "OE2TEST123456",
    "PartyA": "174379",
    "IdentifierType": "4",
    "ResultURL": ts_result,
    "QueueTimeOutURL": ts_timeout,
    "Remarks": "Smoke test",
    "Occasion": "Smoke test"
}
resp = requests.post("https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query",
                     json=payload,
                     headers={"Authorization": f"Bearer {token}"}, timeout=20)
print("\n--- DARAJA RESPONSE ---")
print(resp.status_code)
print(resp.text)
if resp.status_code==200 and '"ResponseCode":"0"' in resp.text:
    print("\n✅✅✅ SMOKE TEST PASSED - Status request is NOW WORKING!")
else:
    print("\nCheck response above - if Invalid SecurityCredential, your certificate_pem in DB is wrong")
