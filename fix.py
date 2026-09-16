import pathlib
p=pathlib.Path("app.py").read_text()
# Fix: make stk push always return JSON not HTML
p=p.replace('return f"<h1>Error: {e}</h1>"', 'return __import__("flask").jsonify({"error": str(e)}), 500')
# If that pattern not found, force patch the generic error handler
if 'Unexpected token' not in p:
    p=p.replace(
        'except Exception as e:\n print("STK ERROR:"',
        'except Exception as e:\n import traceback, flask\n print("STK ERROR:", str(e))\n traceback.print_exc()\n return flask.jsonify({"error": str(e)}), 500\n print("OLD"'
    )
# Ensure sandbox Daraja exists so it doesn't crash
p=p.replace('jsonify({"error": "Daraja not configured"})', 'jsonify({"error": "Go to /daraja and save your Consumer Key/Secret/Passkey first - using sandbox 174379"})')

# Auto-insert sandbox default if DB empty
open("auto_config.py","w").write("""
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
""")
pathlib.Path("app.py").write_text(p)
print("patched app.py")
