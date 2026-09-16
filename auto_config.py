
import sqlite3, os
os.makedirs("instance", exist_ok=True)
db="instance/schoolpay.db"
if os.path.exists(db):
    con=sqlite3.connect(db); cur=con.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM daraja_config")
        if cur.fetchone()[0]==0:
            cur.execute("INSERT INTO daraja_config (consumer_key,consumer_secret,shortcode,passkey,env,callback_url,validation_url,confirmation_url) VALUES (?,?,?,?,?,?,?,?)",
            ('YOUR_CONSUMER_KEY','YOUR_CONSUMER_SECRET','174379','bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919','sandbox','https://eca375479d50e3.lhr.life/mpesa/callback','https://eca375479d50e3.lhr.life/mpesa/c2b/validation','https://eca375479d50e3.lhr.life/mpesa/c2b/confirmation'))
            con.commit(); print("Inserted sandbox daraja placeholder - EDIT KEYS in /daraja")
    except Exception as e: print("config skip", e)
    con.close()
