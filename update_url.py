import pathlib
new_url = "https://guam-restricted-arrange-after.trycloudflare.com"
new_callback = f"{new_url}/mpesa_callback/SchoolPay2026Secret"
# update config.env
content = pathlib.Path("config.env").read_text()
content = content.replace(content.split("MPESA_CALLBACK_URL=")[1].split("\n")[0], new_callback)
# safer rewrite
lines=[]
for line in content.splitlines():
    if line.startswith("MPESA_CALLBACK_URL="):
        lines.append(f"MPESA_CALLBACK_URL={new_callback}")
    else:
        lines.append(line)
pathlib.Path("config.env").write_text("\n".join(lines)+"\n")
print(f"[✓] Updated to {new_callback}")

# update db
import sqlite3, pathlib
for db_path in list(pathlib.Path(".").rglob("*.db")):
    try:
        conn=sqlite3.connect(db_path)
        cur=conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for (t,) in cur.fetchall():
            if "daraja" in t.lower() or "mpesa" in t.lower() or "config" in t.lower():
                try:
                    cur.execute(f"UPDATE {t} SET callback_url=?, c2b_validation_url=?, c2b_confirmation_url=?", (new_callback, f"{new_url}/mpesa/c2b/validation", f"{new_url}/mpesa/c2b/confirmation"))
                    conn.commit()
                    print(f"[✓] DB {db_path}:{t} updated")
                except: pass
        conn.close()
    except: pass
