import os, base64, json, requests, datetime
from flask import Flask, request, render_template_string, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "SchoolPay2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schoolpay.db'
db = SQLAlchemy(app)

class Config(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    shortcode=db.Column(db.String(20),default="174379")
    env=db.Column(db.String(20),default="sandbox")
    passkey=db.Column(db.String(200),default="bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
    consumer_key=db.Column(db.String(200),default="")
    consumer_secret=db.Column(db.String(200),default="")
    callback_url=db.Column(db.String(500),default="")

class Payment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    phone=db.Column(db.String(20)); amount=db.Column(db.Integer)
    account=db.Column(db.String(100)); status=db.Column(db.String(20),default="PENDING")
    mpesa_code=db.Column(db.String(50))
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()
    if not Config.query.first():
        db.session.add(Config()); db.session.commit()

def get_cfg():
    c=Config.query.first()
    base=request.host_url.rstrip("/") if request else ""
    if base and ("lhr.life" in (c.callback_url or "") or not c.callback_url):
        c.callback_url=base+"/mpesa/callback"
        db.session.commit()
    return c

def daraja_token(cfg):
    url="https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials" if cfg.env=="sandbox" else "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r=requests.get(url,auth=(cfg.consumer_key,cfg.consumer_secret),timeout=20)
    r.raise_for_status(); return r.json()['access_token']

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form['username']=='admin' and request.form['password']=='admin123':
            session['admin']=True; return redirect('/')
        return "Wrong"
    return '<h2>Login</h2><form method=post><input name=username><input name=password type=password><button>Login</button></form> admin/admin123'

@app.route('/')
def index():
    if not session.get('admin'): return redirect('/login')
    return f'<h2>SchoolPay OK</h2>Callback: {request.host_url}mpesa/callback<br><a href=/daraja>Config</a> | <a href=/payments>Payments</a><hr><form action=/stk_push method=post>Phone 254...:<input name=phone value=254708374149><br>Amount:<input name=amount value=10><br>Acc:<input name=account value=Student001><br><button>STK Push</button></form>'

@app.route('/daraja',methods=['GET','POST'])
def daraja():
    if not session.get('admin'): return redirect('/login')
    cfg=get_cfg()
    if request.method=='POST':
        cfg.shortcode=request.form['shortcode']; cfg.env=request.form['env']; cfg.passkey=request.form['passkey']; cfg.consumer_key=request.form['consumer_key']; cfg.consumer_secret=request.form['consumer_secret']; cfg.callback_url=request.form['callback_url']; db.session.commit(); return redirect('/')
    return render_template_string('<form method=post>Shortcode:<input name=shortcode value="{{c.shortcode}}"><br>Env:<select name=env><option value=sandbox> sandbox</option><option value=production>production</option></select><br>Passkey:<input name=passkey value="{{c.passkey}}" style=width:400px><br>Key:<input name=consumer_key value="{{c.consumer_key}}" style=width:400px><br>Secret:<input name=consumer_secret value="{{c.consumer_secret}}" style=width:400px><br>Callback:<input name=callback_url value="{{c.callback_url}}" style=width:400px><br><button>Save</button></form>',c=cfg)

@app.route('/stk_push',methods=['POST'])
def stk():
    cfg=get_cfg()
    try:
        token=daraja_token(cfg)
        ts=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        pwd=base64.b64encode((cfg.shortcode+cfg.passkey+ts).encode()).decode()
        phone=request.form['phone']; amount=request.form['amount']; acc=request.form['account']
        url="https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest" if cfg.env=="sandbox" else "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        payload={"BusinessShortCode":cfg.shortcode,"Password":pwd,"Timestamp":ts,"TransactionType":"CustomerPayBillOnline","Amount":int(amount),"PartyA":phone,"PartyB":cfg.shortcode,"PhoneNumber":phone,"CallBackURL":cfg.callback_url or request.host_url+"mpesa/callback","AccountReference":acc,"TransactionDesc":"Fees"}
        r=requests.post(url,json=payload,headers={"Authorization":f"Bearer {token}"},timeout=30)
        p=Payment(phone=phone,amount=amount,account=acc,status=str(r.json())); db.session.add(p); db.session.commit()
        return jsonify(r.json()),r.status_code
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/mpesa/callback',methods=['POST'])
def cb():
    print(request.get_json()); return jsonify({"ResultCode":0,"ResultDesc":"Accepted"})

@app.route('/payments')
def pays():
    ps=Payment.query.order_by(Payment.id.desc()).all()
    h="<table border=1>"; 
    for x in ps: h+=f"<tr><td>{x.phone}</td><td>{x.amount}</td><td>{x.status}</td></tr>"
    return h+"</table>"

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.getenv("PORT",5000)))
