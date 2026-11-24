from flask import Flask, request, redirect, session
import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)

con = sqlite3.connect("pos.db")
con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
con.execute(
    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
    ("app_secret", secrets.token_hex(32))
)
app.secret_key = con.execute(
    "SELECT value FROM settings WHERE key='app_secret'"
).fetchone()[0]
con.commit()
con.close()

def db():
    return sqlite3.connect("pos.db")


@app.route("/owner_setup", methods=["GET", "POST"])
def owner_setup():
    con = db()
    exists = con.execute(
        "SELECT value FROM settings WHERE key='owner_password'"
    ).fetchone()

    if exists:
        con.close()
        return "Owner Password ရှိပြီးသားပါ။"

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(password) < 6 or password != confirm:
            con.close()
            return "Password အနည်းဆုံး ၆ လုံးဖြစ်ရမယ်၊ နှစ်ခုတူရမယ်။ <a href='/owner_setup'>ပြန်ကြိုးစားရန်</a>"

        hashed = generate_password_hash(password)
        con.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("owner_password", hashed)
        )
        con.commit()
        con.close()
        return "Owner Password သတ်မှတ်ပြီးပါပြီ။ <a href='/owner_login'>Login ဝင်ရန်</a>"

    con.close()
    return """
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <h2>Owner Password သတ်မှတ်ရန်</h2>
    <form method="POST">
      <input name="password" type="password" placeholder="Password အနည်းဆုံး ၆ လုံး" required>
      <br><br>
      <input name="confirm" type="password" placeholder="Password ထပ်ထည့်ရန်" required>
      <br><br>
      <button type="submit">Password သိမ်းမယ်</button>
    </form>
    """


@app.route("/owner_login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        con = db()
        row = con.execute(
            "SELECT value FROM settings WHERE key='owner_password'"
        ).fetchone()
        con.close()

        if row and check_password_hash(row[0], password):
            session["owner"] = True
            return redirect("/products")

        return "Password မှားနေပါတယ်။ <a href='/owner_login'>ပြန်ဝင်ရန်</a>"

    return """
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <h2>Owner Login</h2>
    <form method="POST">
      <input name="password" type="password" placeholder="Owner Password" required>
      <br><br>
      <button type="submit">Login</button>
    </form>
    """


@app.route("/owner_logout")
def owner_logout():
    session.pop("owner", None)
    return redirect("/owner_login")


def owner_required():
    return session.get("owner") is True



@app.route("/products")
def products():
    if not owner_required():
        return redirect("/owner_login")

    con = db()
    data = con.execute(
        "SELECT id, name, cost, price, stock FROM products WHERE active=1 ORDER BY id DESC"
    ).fetchall()
    con.close()

    rows = ""
    for item in data:
        name = str(item[1]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        rows += f"""
        <tr>
          <td>{item[0]}</td>
          <td>{name}</td>
          <td>{item[2]:,.0f}</td>
          <td>{item[3]:,.0f}</td>
          <td>{item[4]}</td>
          <td>
            <form method="POST" action="/product_save">
              <input type="hidden" name="id" value="{item[0]}">
              <input name="name" value="{name}" required>
              <input name="cost" type="number" min="0" step="1" value="{item[2]}" required>
              <input name="price" type="number" min="0" step="1" value="{item[3]}" required>
              <input name="stock" type="number" min="0" step="1" value="{item[4]}" required>
              <button>ပြင်ဆင်သိမ်းမယ်</button>
            </form>
            <form method="POST" action="/product_delete">
              <input type="hidden" name="id" value="{item[0]}">
              <button style="background:#dc2626;color:white">ဖျက်မယ်</button>
            </form>
          </td>
        </tr>
        """

    return f"""
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ပစ္စည်းစီမံခန့်ခွဲမှု</title>
    <style>
    body{{font-family:Arial;padding:15px;background:#f3f4f6}}
    input{{padding:9px;margin:4px;max-width:130px}}
    button{{padding:9px;margin:4px;background:#16a34a;color:white;border:0;border-radius:6px}}
    table{{background:white;border-collapse:collapse;width:100%}}
    th,td{{padding:8px;border:1px solid #ddd;text-align:left}}
    </style></head><body>
    <h2>📦 ပစ္စည်းစီမံခန့်ခွဲမှု</h2>
    <h3>ပစ္စည်းအသစ်ထည့်ရန်</h3>
    <form method="POST" action="/product_save">
      <input name="name" placeholder="ပစ္စည်းအမည်" required>
      <input name="cost" type="number" min="0" step="1" placeholder="အရင်းဈေး" required>
      <input name="price" type="number" min="0" step="1" placeholder="ရောင်းဈေး" required>
      <input name="stock" type="number" min="0" step="1" placeholder="လက်ကျန်" required>
      <button>ပစ္စည်းထည့်မယ်</button>
    </form>
    <h3>ပစ္စည်းစာရင်း</h3>
    <p>ID | အမည် | အရင်းဈေး | ရောင်းဈေး | လက်ကျန်</p>
    <table><tr><th>ID</th><th>အမည်</th><th>အရင်း</th><th>ရောင်း</th><th>လက်ကျန်</th><th>ပြင်/ဖျက်</th></tr>
    {rows}</table>
    <p><a href="/owner_logout">Logout</a> | <a href="/rooms_live">KTV အခန်းများ</a></p>
</body></html>
    """


@app.route("/product_save", methods=["POST"])
def product_save():
    if not owner_required():
        return redirect("/owner_login")

    name = request.form.get("name", "").strip()
    try:
        cost = float(request.form.get("cost", 0))
        price = float(request.form.get("price", 0))
        stock = int(request.form.get("stock", 0))
    except ValueError:
        return "ဈေးနှုန်းနှင့် လက်ကျန်ကို မှန်ကန်စွာ ထည့်ပါ။"

    if not name or cost < 0 or price < 0 or stock < 0:
        return "အချက်အလက်များကို မှန်ကန်စွာ ထည့်ပါ။"

    product_id = request.form.get("id")
    con = db()

    if product_id:
        con.execute(
            "UPDATE products SET name=?, cost=?, price=?, stock=? WHERE id=?",
            (name, cost, price, stock, product_id)
        )
    else:
        con.execute(
            "INSERT INTO products (name, cost, price, stock) VALUES (?, ?, ?, ?)",
            (name, cost, price, stock)
        )

    con.commit()
    con.close()
    return redirect("/products")


@app.route("/product_delete", methods=["POST"])
def product_delete():
    if not owner_required():
        return redirect("/owner_login")

    product_id = request.form.get("id")
    con = db()
    con.execute(
        "UPDATE products SET active=0 WHERE id=?",
        (product_id,)
    )
    con.commit()
    con.close()
    return redirect("/products")



@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="my">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shine KTV</title>
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#101010">
<style>
*{box-sizing:border-box}
body{margin:0;padding:18px;background:#101010;color:white;font-family:Arial,sans-serif}
header{text-align:center;padding:25px 10px}
h1{color:#f2c14e;font-size:32px;letter-spacing:3px;margin:8px}
header p{color:#aaa}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}
a{color:white;text-decoration:none}
.card{background:#202020;border:1px solid #8c681c;border-radius:15px;padding:22px 10px;text-align:center;min-height:110px}
.card .emoji{font-size:30px;display:block;margin-bottom:10px}
.card strong{font-size:15px}
.rooms{background:#8c681c;border:0}
footer{text-align:center;color:#777;margin-top:30px;font-size:12px}
@media(min-width:600px){.grid{grid-template-columns:repeat(3,1fr)}}
</style>
</head>
<body>
<header>
<h1>★ SHINE KTV ★</h1>
<p>Management System</p>
</header>

<div class="grid">
<a href="/rooms_live"><div class="card rooms"><span class="emoji">🎤</span><strong>KTV အခန်း ၁၅ ခန်း</strong></div></a>
<a href="/rooms"><div class="card"><span class="emoji">💰</span><strong>အခန်းဈေးနှုန်း</strong></div></a>
<a href="/products"><div class="card"><span class="emoji">🥤</span><strong>ပစ္စည်းစီမံခန့်ခွဲမှု</strong></div></a>
<a href="/dashboard"><div class="card"><span class="emoji">📊</span><strong>Dashboard / အမြတ်စာရင်း</strong></div></a>
<a href="/reports"><div class="card"><span class="emoji">📄</span><strong>အရောင်းအစီရင်ခံစာ</strong></div></a>
<a href="/room_payments"><div class="card"><span class="emoji">🧾</span><strong>ငွေရှင်းမှတ်တမ်း</strong></div></a>
</div>

<footer>SHINE KTV POS © 2026</footer>

<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function() {
    navigator.serviceWorker.register("/static/sw.js");
  });
}
</script>
</body>
</html>
"""


def init_rooms():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            room_type TEXT,
            price REAL DEFAULT 0,
            status TEXT DEFAULT 'လွတ်'
        )
    """)
    for i in range(1, 16):
        kind = "ရှယ်ခန်း" if i <= 5 else "ပုံမှန်ခန်း"
        con.execute(
            "INSERT OR IGNORE INTO rooms (id, room_type) VALUES (?, ?)",
            (i, kind)
        )
    con.commit()
    con.close()

@app.route("/rooms")
def rooms():
    init_rooms()
    con = db()
    data = con.execute("SELECT * FROM rooms ORDER BY id").fetchall()
    con.close()

    rows = ""
    for r in data:
        rows += f"""
        <tr>
        <td>Room {r[0]:02d}</td>
        <td>{r[1]}</td>
        <td>{r[3]}</td>
        <td>
        <form method="POST" action="/room_price/{r[0]}">
        <input name="price" type="number" value="{r[2]}" min="0">
        <button>Save</button>
        </form>
        </td>
        </tr>
        """

    return """
    <html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>KTV Rooms</title>
    <style>
    body{background:#101827;color:white;font-family:Arial;padding:15px}
    table{width:100%;border-collapse:collapse}
    td,th{padding:8px;border-bottom:1px solid #475569}
    input{width:75px;padding:8px}
    button{padding:8px;background:#0284c7;color:white;border:0}
    a{color:#38bdf8}
    </style></head><body>
    <h2>KTV Room Management</h2>
    <p>အခန်း ၁၅ ခန်း | ရှယ်ခန်း ၅ ခန်း | ပုံမှန်ခန်း ၁၀ ခန်း</p>
    <table><tr><th>Room</th><th>Type</th><th>Status</th><th>Price</th></tr>
    """ + rows + """
    </table>
    <p><a href="/">Back to POS</a></p>
    </body></html>
    """

@app.route("/room_price/<int:room_id>", methods=["POST"])
def room_price(room_id):
    price = request.form.get("price", 0)
    try:
        price = max(0, float(price))
    except ValueError:
        price = 0
    con = db()
    con.execute("UPDATE rooms SET price=? WHERE id=?", (price, room_id))
    con.commit()
    con.close()
    return redirect("/rooms")



@app.route("/room_start/<int:room_id>")
def room_start(room_id):
    con = db()
    con.execute(
        "UPDATE rooms SET status='အသုံးပြုနေ', started_at=?, ended_at=NULL WHERE id=? AND status='လွတ်'",
        (datetime.now().isoformat(timespec="seconds"), room_id)
    )
    con.commit()
    con.close()
    return redirect("/rooms")



@app.route("/room_end/<int:room_id>")
def room_end(room_id):
    con = db()
    room = con.execute(
        "SELECT id, room_type, price, started_at, ended_at, bill_total, bill_hours, bill_minutes, status FROM rooms WHERE id=?",
        (room_id,)
    ).fetchone()

    if not room:
        con.close()
        return redirect("/rooms_live")

    if room[8] == "အသုံးပြုနေ" and room[3]:
        start_time = datetime.fromisoformat(room[3])
        end_time = datetime.now()
        minutes = int(max(0, (end_time - start_time).total_seconds() / 60))
        hours = max(1, (minutes + 59) // 60)
        room_total = hours * room[2]

        con.execute(
            """UPDATE rooms SET status='ငွေရှင်းရန်', ended_at=?,
            bill_total=?, bill_hours=?, bill_minutes=? WHERE id=?""",
            (end_time.isoformat(timespec="seconds"), room_total, hours, minutes, room_id)
        )
        con.commit()
        room = con.execute(
            "SELECT id, room_type, price, started_at, ended_at, bill_total, bill_hours, bill_minutes, status FROM rooms WHERE id=?",
            (room_id,)
        ).fetchone()

    if room[8] != "ငွေရှင်းရန်":
        con.close()
        return redirect("/rooms_live")

    product_total = con.execute(
        """SELECT COALESCE(SUM(total),0) FROM room_orders
        WHERE room_id=? AND created_at>=?""",
        (room_id, room[3] or "")
    ).fetchone()[0]

    settings = dict(con.execute(
        "SELECT key, value FROM settings WHERE key IN ('service_percent','discount_percent')"
    ).fetchall())
    service_percent = max(0, float(settings.get("service_percent", "5")))
    discount_percent = min(100, max(0, float(settings.get("discount_percent", "0"))))

    subtotal = room[5] + product_total
    service_fee = round(subtotal * service_percent / 100)
    discount = round(subtotal * discount_percent / 100)
    grand_total = max(0, subtotal + service_fee - discount)
    con.close()

    return f"""
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Room {room_id:02d} ငွေရှင်းရန်</title></head>
    <body style="font-family:Arial;padding:20px;background:#f3f4f6">
    <div style="background:white;padding:20px;border-radius:12px;max-width:500px;margin:auto">
    <h2>Room {room_id:02d} ငွေရှင်းရန်</h2>
    <p>အခန်းအမျိုးအစား: {room[1]}</p>
    <p>အသုံးပြုချိန်: {room[7]} မိနစ် ({room[6]} နာရီ)</p>
    <hr>
    <p>အခန်းခ: {room[5]:,.0f} ကျပ်</p>
    <p>ပစ္စည်းဖိုး: {product_total:,.0f} ကျပ်</p>
    <p>စုစုပေါင်း: {subtotal:,.0f} ကျပ်</p>
    <p>Service Fee ({service_percent:g}%): {service_fee:,.0f} ကျပ်</p>
    <p>Discount ({discount_percent:g}%): -{discount:,.0f} ကျပ်</p>
    <hr>
    <h2>ကျသင့်ငွေ: {grand_total:,.0f} ကျပ်</h2>
    <form method="POST" action="/room_paid/{room_id}">
    <label>ငွေပေးချေမှုနည်းလမ်း</label><br>
    <select name="payment_method" style="padding:12px;width:100%;margin:10px 0">
      <option>Cash</option>
      <option>KPay</option>
      <option>Wave Pay</option>
      <option>Bank Transfer</option>
      <option>Other</option>
    </select><br>
    <button style="background:#16a34a;color:white;padding:16px;width:100%;border:0;border-radius:10px;font-size:18px">
    ငွေလက်ခံပြီးပါပြီ
    </button></form>
    <p><a href="/rooms_live">အခန်းများသို့ ပြန်သွားရန်</a></p>
    </div></body></html>
    """


@app.route("/room_paid/<int:room_id>", methods=["POST"])
def room_paid(room_id):
    con = db()
    room = con.execute(
        """SELECT id, room_type, price, started_at, ended_at,
        bill_total, bill_hours, bill_minutes FROM rooms
        WHERE id=? AND status='ငွေရှင်းရန်'""",
        (room_id,)
    ).fetchone()

    if not room:
        con.close()
        return redirect("/rooms_live")

    product_total = con.execute(
        """SELECT COALESCE(SUM(total),0) FROM room_orders
        WHERE room_id=? AND created_at>=?""",
        (room_id, room[3] or "")
    ).fetchone()[0]

    settings = dict(con.execute(
        "SELECT key, value FROM settings WHERE key IN ('service_percent','discount_percent')"
    ).fetchall())
    service_percent = max(0, float(settings.get("service_percent", "5")))
    discount_percent = min(100, max(0, float(settings.get("discount_percent", "0"))))

    subtotal = room[5] + product_total
    service_fee = round(subtotal * service_percent / 100)
    discount = round(subtotal * discount_percent / 100)
    grand_total = max(0, subtotal + service_fee - discount)

    payment_method = request.form.get("payment_method", "Cash")
    allowed_methods = ("Cash", "KPay", "Wave Pay", "Bank Transfer", "Other")
    if payment_method not in allowed_methods:
        payment_method = "Cash"

    con.execute(
        """INSERT INTO room_payments
        (room_id, room_type, started_at, ended_at, minutes, hours, rate,
         total, paid_at, product_total, service_fee, discount, grand_total, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (room[0], room[1], room[3], room[4], room[7], room[6], room[2],
         grand_total, datetime.now().isoformat(timespec="seconds"),
         product_total, service_fee, discount, grand_total, payment_method)
    )

    con.execute(
        """UPDATE rooms SET status='လွတ်', started_at=NULL, ended_at=NULL,
        bill_total=0, bill_hours=0, bill_minutes=0 WHERE id=?""",
        (room_id,)
    )
    con.commit()
    con.close()
    return redirect("/rooms_live")



@app.route("/dashboard")
def dashboard():
    if not owner_required():
        return redirect("/owner_login")

    con = db()

    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    def payment_stats(condition, value):
        return con.execute(
            f"""SELECT COALESCE(SUM(grand_total),0),
                       COALESCE(SUM(rate * hours),0),
                       COALESCE(SUM(product_total),0),
                       COALESCE(SUM(service_fee),0),
                       COALESCE(SUM(discount),0)
                FROM room_payments WHERE {condition}""",
            (value,)
        ).fetchone()

    day = payment_stats("date(paid_at)=?", today)
    monthly = payment_stats("strftime('%Y-%m', paid_at)=?", month)

    def product_profit(condition, value):
        return con.execute(
            f"""SELECT COALESCE(SUM((ro.price-ro.cost)*ro.quantity),0)
                FROM room_orders ro
                JOIN room_payments rp ON rp.room_id=ro.room_id
                WHERE {condition}
                AND ro.created_at >= rp.started_at
                AND ro.created_at <= rp.ended_at""",
            (value,)
        ).fetchone()[0]

    day_product_profit = product_profit("date(rp.paid_at)=?", today)
    month_product_profit = product_profit("strftime('%Y-%m',rp.paid_at)=?", month)

    day_expense = con.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date(created_at)=?",
        (today,)
    ).fetchone()[0]

    month_expense = con.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE strftime('%Y-%m',created_at)=?",
        (month,)
    ).fetchone()[0]

    recent = con.execute(
        "SELECT id, description, amount, created_at FROM expenses ORDER BY id DESC LIMIT 20"
    ).fetchall()

    con.close()

    day_net = day[1] + day_product_profit + day[3] - day[4] - day_expense
    month_net = monthly[1] + month_product_profit + monthly[3] - monthly[4] - month_expense

    expense_rows = "".join(
        f"""<tr><td>{r[1]}</td><td>{r[2]:,.0f}</td><td>{r[3]}</td>
        <td><form method="POST" action="/expense_delete/{r[0]}"
        onsubmit="return confirm('ဒီအသုံးစရိတ်ကို ဖျက်မှာ သေချာပါသလား?')">
        <button style="background:#dc2626">ဖျက်မယ်</button></form></td></tr>"""
        for r in recent
    )

    return f"""
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>KTV Dashboard</title>
    <style>
    body{{font-family:Arial;background:#f3f4f6;padding:15px}}
    .card{{background:white;padding:15px;margin:10px 0;border-radius:12px}}
    .number{{font-size:23px;font-weight:bold;color:#15803d}}
    input{{padding:12px;margin:5px;max-width:95%}}
    button{{padding:12px;background:#16a34a;color:white;border:0;border-radius:7px}}
    table{{width:100%;background:white;border-collapse:collapse}}
    td,th{{padding:9px;border:1px solid #ddd;text-align:left}}
    </style></head><body>
    <h2>📊 KTV Dashboard</h2>
    <h3>ယနေ့ ({today})</h3>
    <div class="card">စုစုပေါင်းဝင်ငွေ<div class="number">{day[0]:,.0f} ကျပ်</div></div>
    <div class="card">အခန်းခဝင်ငွေ<div class="number">{day[1]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းရောင်းရငွေ<div class="number">{day[2]:,.0f} ကျပ်</div></div>
    <div class="card">Service Fee<div class="number">{day[3]:,.0f} ကျပ်</div></div>
    <div class="card">Discount<div class="number">{day[4]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းအမြတ်<div class="number">{day_product_profit:,.0f} ကျပ်</div></div>
    <div class="card">အသုံးစရိတ်<div class="number">{day_expense:,.0f} ကျပ်</div></div>
    <div class="card">အသားတင်အမြတ်<div class="number">{day_net:,.0f} ကျပ်</div></div>

    <h3>ယခုလ ({month})</h3>
    <div class="card">စုစုပေါင်းဝင်ငွေ<div class="number">{monthly[0]:,.0f} ကျပ်</div></div>
    <div class="card">အခန်းခဝင်ငွေ<div class="number">{monthly[1]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းရောင်းရငွေ<div class="number">{monthly[2]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းအမြတ်<div class="number">{month_product_profit:,.0f} ကျပ်</div></div>
    <div class="card">အသုံးစရိတ်<div class="number">{month_expense:,.0f} ကျပ်</div></div>
    <div class="card">အသားတင်အမြတ်<div class="number">{month_net:,.0f} ကျပ်</div></div>

    <h3>အသုံးစရိတ် အသစ်ထည့်ရန်</h3>
    <form method="POST" action="/expense_add" class="card">
      <input name="description" placeholder="အသုံးစရိတ်အကြောင်း" required>
      <input name="amount" type="number" min="1" step="1" placeholder="ငွေပမာဏ" required>
      <button>သိမ်းမယ်</button>
    </form>

    <h3>အသုံးစရိတ်မှတ်တမ်း</h3>
    <table><tr><th>အကြောင်းအရာ</th><th>ငွေ</th><th>နေ့စွဲ</th><th>လုပ်ဆောင်ချက်</th></tr>
    {expense_rows}
    </table>
    <p><a href="/products">ပစ္စည်းများ</a> |
       <a href="/rooms_live">KTV အခန်းများ</a> |
       <a href="/room_payments">ငွေရှင်းမှတ်တမ်း</a> |
       <a href="/owner_logout">Logout</a></p>
    </body></html>
    """


@app.route("/expense_add", methods=["POST"])
def expense_add():
    if not owner_required():
        return redirect("/owner_login")

    description = request.form.get("description", "").strip()
    try:
        amount = float(request.form.get("amount", "0"))
    except ValueError:
        return "အသုံးစရိတ်ပမာဏ မှားနေပါသည်။"

    if not description or amount <= 0:
        return "အချက်အလက် မှန်ကန်စွာ ထည့်ပါ။"

    con = db()
    con.execute(
        "INSERT INTO expenses (description, amount, created_at) VALUES (?, ?, ?)",
        (description, amount, datetime.now().isoformat(timespec="seconds"))
    )
    con.commit()
    con.close()
    return redirect("/dashboard")


@app.route("/expense_delete/<int:expense_id>", methods=["POST"])
def expense_delete(expense_id):
    if not owner_required():
        return redirect("/owner_login")

    con = db()
    con.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    con.commit()
    con.close()
    return redirect("/dashboard")


@app.route("/room_order/<int:room_id>")
def room_order(room_id):
    con = db()
    room = con.execute(
        "SELECT id, status, started_at FROM rooms WHERE id=?",
        (room_id,)
    ).fetchone()

    if not room:
        con.close()
        return "အခန်းမတွေ့ပါ။"

    if room[1] != "အသုံးပြုနေ":
        con.close()
        return f"<h3>Room {room_id:02d} ကို အရင်ဖွင့်ပေးပါ။</h3><a href='/rooms_live'>အခန်းများသို့ပြန်သွားရန်</a>"

    products = con.execute(
        "SELECT id, name, price, stock FROM products WHERE active=1 AND stock>0 ORDER BY name"
    ).fetchall()

    orders = con.execute(
        """SELECT p.name, ro.quantity, ro.price, ro.total
           FROM room_orders ro
           JOIN products p ON p.id=ro.product_id
           WHERE ro.room_id=? AND ro.created_at>=?
           ORDER BY ro.id DESC""",
        (room_id, room[2] or "")
    ).fetchall()
    con.close()

    product_html = ""
    for item in products:
        name = str(item[1]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        product_html += f"""
        <form method="POST" action="/room_order_add/{room_id}" style="background:white;padding:12px;margin:10px 0;border-radius:10px">
          <b>{name}</b><br>
          ရောင်းဈေး - {item[2]:,.0f} ကျပ် | လက်ကျန် - {item[3]}<br>
          <input type="hidden" name="product_id" value="{item[0]}">
          <input type="number" name="quantity" min="1" max="{item[3]}" value="1" required>
          <button>အမှာစာထည့်မယ်</button>
        </form>
        """

    order_html = ""
    total = 0
    for item in orders:
        order_html += f"<tr><td>{item[0]}</td><td>{item[1]}</td><td>{item[2]:,.0f}</td><td>{item[3]:,.0f}</td></tr>"
        total += item[3]

    return f"""
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Room {room_id:02d} အမှာစာ</title>
    <style>
    body{{font-family:Arial;background:#f3f4f6;padding:15px}}
    input{{padding:10px;width:75px;margin-top:8px}}
    button{{padding:10px 16px;background:#16a34a;color:white;border:0;border-radius:7px;margin:5px}}
    table{{width:100%;background:white;border-collapse:collapse}}
    td,th{{padding:9px;border:1px solid #ddd;text-align:left}}
    </style></head><body>
    <h2>🛎️ Room {room_id:02d} ပစ္စည်းမှာယူရန်</h2>
    <h3>ပစ္စည်းစာရင်း</h3>
    {product_html or "လက်ကျန်ပစ္စည်း မရှိသေးပါ။"}
    <h3>ယခုအခန်း၏ အမှာစာများ</h3>
    <table><tr><th>ပစ္စည်း</th><th>အရေအတွက်</th><th>တစ်ခုဈေး</th><th>စုစုပေါင်း</th></tr>
    {order_html}
    </table>
    <h3>ပစ္စည်းဖိုးစုစုပေါင်း - {total:,.0f} ကျပ်</h3>
    <a href="/rooms_live">အခန်းများသို့ ပြန်သွားရန်</a>
    </body></html>
    """


@app.route("/room_order_add/<int:room_id>", methods=["POST"])
def room_order_add(room_id):
    try:
        product_id = int(request.form.get("product_id", "0"))
        quantity = int(request.form.get("quantity", "0"))
    except ValueError:
        return "အရေအတွက် မှားယွင်းနေပါသည်။"

    if product_id <= 0 or quantity <= 0:
        return "အချက်အလက် မှားယွင်းနေပါသည်။"

    con = db()
    try:
        con.execute("BEGIN IMMEDIATE")
        room = con.execute(
            "SELECT status FROM rooms WHERE id=?",
            (room_id,)
        ).fetchone()

        if not room or room[0] != "အသုံးပြုနေ":
            con.rollback()
            con.close()
            return "အခန်းကို အသုံးပြုနေကြောင်း စစ်ဆေးပါ။"

        product = con.execute(
            "SELECT cost, price, stock FROM products WHERE id=? AND active=1",
            (product_id,)
        ).fetchone()

        if not product or product[2] < quantity:
            con.rollback()
            con.close()
            return "ပစ္စည်းလက်ကျန် မလုံလောက်ပါ။"

        cost, price, stock = product
        changed = con.execute(
            "UPDATE products SET stock=stock-? WHERE id=? AND stock>=?",
            (quantity, product_id, quantity)
        ).rowcount

        if changed != 1:
            con.rollback()
            con.close()
            return "ပစ္စည်းလက်ကျန် မလုံလောက်ပါ။"

        con.execute(
            """INSERT INTO room_orders
               (room_id, product_id, quantity, cost, price, total, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (room_id, product_id, quantity, cost, price,
             price * quantity, datetime.now().isoformat())
        )
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise

    con.close()
    return redirect(f"/room_order/{room_id}")


@app.route("/rooms_live")
def rooms_live():
    init_rooms()
    con = db()
    data = con.execute("SELECT * FROM rooms ORDER BY id").fetchall()
    con.close()

    cards = ""
    for r in data:
        room_id = r[0]
        status = r[3]
        if status == "အသုံးပြုနေ":
            color = "#f59e0b"
            action = f"<a class='btn busy' href='/room_end/{room_id}'>ငွေရှင်းရန်</a>"
        elif status == "ငွေရှင်းရန်":
            color = "#ef4444"
            action = f"<a class='btn pending' href='/room_end/{room_id}'>ငွေလက်ခံရန်</a>"
        else:
            color = "#22c55e"
            action = f"<a class='btn free' href='/room_start/{room_id}'>အခန်းစမယ်</a>"

        kind = "VIP" if room_id <= 5 else "NORMAL"
        cards += f"""
        <div class="room">
          <img src="/static/room{room_id:02d}.jpg" alt="Room {room_id}">
          <div class="info">
            <h3>ROOM {room_id:02d}</h3>
            <small>{kind} · {r[1]}</small>
            <p style="color:{color};font-weight:bold">{status}</p>
            <b>{r[2]:,.0f} ကျပ် / နာရီ</b>
            {action}
          </div>
        </div>
        """

    return """
    <!doctype html>
    <html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>KTV Rooms</title>
    <style>
    *{box-sizing:border-box}
    body{margin:0;padding:14px;background:#101827;color:white;font-family:Arial,sans-serif}
    h2{color:#facc15}
    .top{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
    .top a{background:#263449;color:white;padding:11px 15px;border-radius:9px;text-decoration:none}
    .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
    .room{background:#1e293b;border:1px solid #475569;border-radius:12px;overflow:hidden;min-width:0}
    .room img{width:100%;aspect-ratio:1.5;object-fit:cover;display:block}
    .info{padding:9px}
    .info h3{margin:2px 0 5px;color:#facc15;font-size:16px}
    .info small{color:#cbd5e1;font-size:11px}
    .info p{margin:7px 0;font-size:13px}
    .info b{font-size:12px;display:block;margin-bottom:9px}
    .btn{display:block;text-align:center;padding:9px 3px;border-radius:7px;text-decoration:none;color:#111827;font-weight:bold;font-size:12px}
    .free{background:#4ade80}.busy{background:#fbbf24}.pending{background:#f87171}
    @media(max-width:600px){body{padding:8px}.grid{gap:7px}.info{padding:6px}.info h3{font-size:13px}.info small{font-size:9px}.info p{font-size:11px}.info b{font-size:10px}.btn{font-size:10px;padding:8px 2px}}
    </style></head><body>
    <h2>🎤 KTV ROOM MANAGEMENT</h2>
    <div class="top">
      <a href="/room_payments">💰 ငွေစာရင်း</a>
      <a href="/rooms">⚙️ ဈေးနှုန်းပြင်ရန်</a>
    </div>
    <div class="grid">
    """ + cards + """
    </div></body></html>
    """

@app.route("/room_payments")
def room_payments():
    con = db()
    data = con.execute(
        "SELECT room_id, room_type, minutes, hours, rate, total, paid_at FROM room_payments ORDER BY id DESC"
    ).fetchall()
    con.close()

    rows = ""
    grand_total = 0
    for r in data:
        grand_total += r[5] or 0
        rows += f"<tr><td>Room {r[0]:02d}</td><td>{r[1]}</td><td>{r[2]} မိနစ်</td><td>{r[3]} နာရီ</td><td>{r[4]:,.0f}</td><td>{r[5]:,.0f} ကျပ်</td><td>{r[6]}</td></tr>"

    return f"""
    <h2>KTV ငွေလက်ခံမှုမှတ်တမ်း</h2>
    <h3>စုစုပေါင်း: {grand_total:,.0f} ကျပ်</h3>
    <table border="1" cellpadding="8">
    <tr><th>အခန်း</th><th>အမျိုးအစား</th><th>မိနစ်</th><th>နာရီ</th><th>နှုန်း</th><th>ငွေ</th><th>လက်ခံချိန်</th></tr>
    {rows}
    </table>
    <p><a href="/rooms_live">အခန်းများသို့ ပြန်သွားရန်</a></p>
    """

@app.route("/reports")
def reports():
    if not owner_required():
        return redirect("/owner_login")

    period = request.args.get("period", "daily")
    if period == "monthly":
        value = request.args.get("month", datetime.now().strftime("%Y-%m"))
        condition = "strftime('%Y-%m', rp.paid_at)=?"
        expense_condition = "strftime('%Y-%m', created_at)=?"
        selector = '<form><input type="hidden" name="period" value="monthly"><input type="month" name="month" value="' + value + '"><button>ကြည့်မယ်</button></form><a href="/reports">နေ့စဉ် Report</a>'
    else:
        value = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        condition = "date(rp.paid_at)=?"
        expense_condition = "date(created_at)=?"
        selector = '<form><input type="hidden" name="period" value="daily"><input type="date" name="date" value="' + value + '"><button>ကြည့်မယ်</button></form><a href="/reports?period=monthly">လစဉ် Report</a>'

    con = db()
    stats = con.execute(
        f"""SELECT COALESCE(SUM(grand_total),0),
        COALESCE(SUM(rate*hours),0), COALESCE(SUM(product_total),0),
        COALESCE(SUM(service_fee),0), COALESCE(SUM(discount),0)
        FROM room_payments rp WHERE {condition}""", (value,)
    ).fetchone()

    profit = con.execute(
        f"""SELECT COALESCE(SUM((ro.price-ro.cost)*ro.quantity),0)
        FROM room_orders ro JOIN room_payments rp ON rp.room_id=ro.room_id
        WHERE {condition} AND ro.created_at>=rp.started_at
        AND ro.created_at<=rp.ended_at""", (value,)
    ).fetchone()[0]

    expenses = con.execute(
        f"SELECT description,amount,created_at FROM expenses WHERE {expense_condition} ORDER BY id DESC",
        (value,)
    ).fetchall()

    payments = con.execute(
        f"""SELECT room_id,room_type,hours,total,product_total,
        service_fee,discount,grand_total,payment_method,paid_at
        FROM room_payments rp WHERE {condition} ORDER BY id DESC""", (value,)
    ).fetchall()
    con.close()

    expense_total = sum(r[1] or 0 for r in expenses)
    net = stats[1] + profit + stats[3] - stats[4] - expense_total

    payment_rows = "".join(
        f"<tr><td>Room {r[0]:02d}</td><td>{r[1]}</td><td>{r[2]}</td><td>{(r[3] or 0):,.0f}</td><td>{(r[4] or 0):,.0f}</td><td>{(r[5] or 0):,.0f}</td><td>{(r[6] or 0):,.0f}</td><td>{(r[7] or 0):,.0f}</td><td>{r[8]}</td><td>{r[9]}</td></tr>"
        for r in payments
    ) or '<tr><td colspan="10">မှတ်တမ်းမရှိပါ</td></tr>'

    expense_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]:,.0f}</td><td>{r[2]}</td></tr>"
        for r in expenses
    ) or '<tr><td colspan="3">အသုံးစရိတ်မရှိပါ</td></tr>'

    return f"""
    <html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    body{{font-family:Arial,sans-serif;padding:15px;background:#f3f4f6}}
    .card{{background:white;padding:14px;margin:9px 0;border-radius:10px}}
    .num{{font-size:21px;font-weight:bold;color:green}}
    table{{border-collapse:collapse;width:100%;background:white}}
    th,td{{border:1px solid #ccc;padding:8px;font-size:13px}}
    .wrap{{overflow-x:auto}}
    button{{padding:12px;background:green;color:white;border:0;border-radius:7px}}
    @media print{{.noprint{{display:none}}body{{background:white}}}}
    </style></head><body>
    <div class="noprint">
    <h2 style="color:#b8860b;font-size:30px;letter-spacing:3px">★ SHINE KTV ★</h2><h3>အရောင်းအစီရင်ခံစာ</h3>
    {selector}
    <button onclick="window.print()">PDF သိမ်းရန် / Print</button>
    <a href="/dashboard">Dashboard</a>
    </div>
    <h2 style="color:#b8860b;font-size:30px;letter-spacing:3px">★ SHINE KTV ★</h2><h3>အရောင်းအစီရင်ခံစာ</h3><h3>{value}</h3>
    <div class="card">စုစုပေါင်းဝင်ငွေ<div class="num">{stats[0]:,.0f} ကျပ်</div></div>
    <div class="card">အခန်းခဝင်ငွေ<div class="num">{stats[1]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းရောင်းရငွေ<div class="num">{stats[2]:,.0f} ကျပ်</div></div>
    <div class="card">ပစ္စည်းအမြတ်<div class="num">{profit:,.0f} ကျပ်</div></div>
    <div class="card">Service Fee<div class="num">{stats[3]:,.0f} ကျပ်</div></div>
    <div class="card">Discount<div class="num">{stats[4]:,.0f} ကျပ်</div></div>
    <div class="card">အသုံးစရိတ်<div class="num">{expense_total:,.0f} ကျပ်</div></div>
    <div class="card">အသားတင်အမြတ်<div class="num">{net:,.0f} ကျပ်</div></div>
    <h3>ငွေရှင်းမှတ်တမ်း</h3><div class="wrap"><table>
    <tr><th>အခန်း</th><th>အမျိုးအစား</th><th>နာရီ</th><th>အခန်းခ</th><th>ပစ္စည်း</th><th>Service</th><th>Discount</th><th>စုစုပေါင်း</th><th>ငွေလက်ခံနည်း</th><th>အချိန်</th></tr>
    {payment_rows}</table></div>
    <h3>အသုံးစရိတ်မှတ်တမ်း</h3><div class="wrap"><table>
    <tr><th>အကြောင်းအရာ</th><th>ငွေ</th><th>နေ့စွဲ</th></tr>
    {expense_rows}</table></div>
    </body></html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
