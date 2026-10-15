"""MAHAKAL BUILDCON - Flask backend: enquiries -> SQLite + email, plus private manager dashboard."""
import os, re, csv, io, time, secrets, sqlite3, smtplib, threading, hmac
from functools import wraps
from email.message import EmailMessage
from flask import (Flask, render_template, request, jsonify, session,
                   redirect, url_for, abort, Response)
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "enquiries.db")
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)  # set SECRET_KEY in .env so logins survive restarts
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=60 * 60 * 8)  # auto logout after 8 hours

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "")
MANAGER_USER = os.getenv("MANAGER_USER", "")
MANAGER_PASS_HASH = os.getenv("MANAGER_PASS_HASH", "")  # create with: python make_hash.py


def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c


def get_manager():
    with db() as c: return c.execute("SELECT * FROM manager WHERE id=1").fetchone()


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS enquiries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            name TEXT, phone TEXT, email TEXT, project_type TEXT, location TEXT,
            budget TEXT, message TEXT, emailed INTEGER DEFAULT 0, status TEXT DEFAULT 'new')""")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(enquiries)")]
        if "status" not in cols:
            c.execute("ALTER TABLE enquiries ADD COLUMN status TEXT DEFAULT 'new'")
        # manager login lives in the database so it can be changed from the dashboard
        c.execute("CREATE TABLE IF NOT EXISTS manager(id INTEGER PRIMARY KEY CHECK(id=1), username TEXT, password_hash TEXT)")
        if not c.execute("SELECT 1 FROM manager").fetchone() and MANAGER_USER and MANAGER_PASS_HASH:
            c.execute("INSERT INTO manager(id,username,password_hash) VALUES(1,?,?)", (MANAGER_USER, MANAGER_PASS_HASH))  # first-run seed from .env


def send_manager_email(eid, d):
    if not (SMTP_USER and SMTP_PASS and MANAGER_EMAIL):
        app.logger.warning("Email not configured - enquiry #%s saved in database only.", eid); return
    msg = EmailMessage()
    msg["Subject"] = f"New Enquiry #{eid} - {d['name']} ({d['type']})"
    msg["From"], msg["To"], msg["Reply-To"] = SMTP_USER, MANAGER_EMAIL, d["email"]
    msg.set_content(f"New website enquiry - MAHAKAL BUILDCON\n\nName: {d['name']}\nPhone: {d['phone']}\n"
                    f"Email: {d['email']}\nProject Type: {d['type']}\nLocation: {d['location'] or '-'}\n"
                    f"Budget: {d['budget'] or '-'}\n\nMessage:\n{d['msg']}\n")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls(); s.login(SMTP_USER, SMTP_PASS); s.send_message(msg)
        with db() as c: c.execute("UPDATE enquiries SET emailed=1 WHERE id=?", (eid,))
    except Exception as e:
        app.logger.error("Email failed for enquiry #%s: %s", eid, e)


# ------------------------- public pages -------------------------
@app.route("/")
@app.route("/index.html")
def home(): return render_template("index.html")

@app.route("/know_more.html")
def know_more(): return render_template("know_more.html")

@app.route("/submit-enquiry", methods=["POST"])
def submit_enquiry():
    f = request.form
    d = {k: (f.get(k) or "").strip()[:2000] for k in ("name", "phone", "email", "type", "location", "budget", "msg")}
    errors = []
    if len(d["name"]) < 2: errors.append("name")
    if not re.fullmatch(r"[+]?[0-9\s-]{10,15}", d["phone"]): errors.append("phone")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", d["email"]): errors.append("email")
    if not d["type"]: errors.append("type")
    if len(d["msg"]) < 10: errors.append("msg")
    if errors: return jsonify(ok=False, errors=errors), 400
    with db() as c:
        eid = c.execute("INSERT INTO enquiries(name,phone,email,project_type,location,budget,message)"
                        " VALUES(?,?,?,?,?,?,?)", (d["name"], d["phone"], d["email"], d["type"],
                        d["location"], d["budget"], d["msg"])).lastrowid
    threading.Thread(target=send_manager_email, args=(eid, d), daemon=True).start()
    return jsonify(ok=True)


# ------------------------- manager area -------------------------
FAILS = {}  # ip -> (count, locked_until)

def csrf_token():
    if "csrf" not in session: session["csrf"] = secrets.token_hex(16)
    return session["csrf"]
app.jinja_env.globals["csrf_token"] = csrf_token

def check_csrf():
    if not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")): abort(400)

def login_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if not session.get("manager"): return redirect(url_for("manager_login"))
        return fn(*a, **k)
    return w

@app.after_request
def no_cache(r):
    if request.path.startswith("/manager"):
        r.headers["Cache-Control"] = "no-store"; r.headers["X-Robots-Tag"] = "noindex"
    return r

@app.route("/manager/login", methods=["GET", "POST"])
def manager_login():
    if session.get("manager"): return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        check_csrf()
        ip = request.remote_addr or "?"
        count, until = FAILS.get(ip, (0, 0))
        if until > time.time():
            error = "Too many attempts. Try again in a few minutes."
        else:
            m = get_manager()
            u_ok = bool(m) and hmac.compare_digest(request.form.get("username", ""), m["username"])
            p_ok = bool(m) and check_password_hash(m["password_hash"], request.form.get("password", ""))
            if u_ok and p_ok:
                FAILS.pop(ip, None); session.clear(); session["manager"] = True; session.permanent = True
                return redirect(url_for("dashboard"))
            count += 1
            FAILS[ip] = (count, time.time() + 600 if count >= 5 else 0)
            error = "Incorrect username or password."
    return render_template("manager_login.html", error=error)

@app.route("/manager/logout", methods=["POST"])
def manager_logout():
    check_csrf(); session.clear(); return redirect(url_for("home"))

def fetch(f="all", q=""):
    sql = ("SELECT *, datetime(created_at,'+5 hours','30 minutes') AS ist FROM enquiries WHERE 1=1")
    args = []
    if f in ("new", "done"): sql += " AND status=?"; args.append(f)
    if q:
        sql += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR project_type LIKE ? OR location LIKE ?)"
        args += [f"%{q}%"] * 5
    with db() as c: return c.execute(sql + " ORDER BY id DESC", args).fetchall()

@app.route("/manager/dashboard")
@login_required
def dashboard():
    f, q = request.args.get("f", "all"), request.args.get("q", "").strip()
    with db() as c:
        total = c.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]
        new = c.execute("SELECT COUNT(*) FROM enquiries WHERE status='new'").fetchone()[0]
    return render_template("manager_dashboard.html", rows=fetch(f, q), f=f, q=q, total=total, new=new)

@app.route("/manager/status/<int:eid>", methods=["POST"])
@login_required
def toggle_status(eid):
    check_csrf()
    with db() as c:
        c.execute("UPDATE enquiries SET status=CASE status WHEN 'new' THEN 'done' ELSE 'new' END WHERE id=?", (eid,))
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/manager/delete/<int:eid>", methods=["POST"])
@login_required
def delete(eid):
    check_csrf()
    with db() as c: c.execute("DELETE FROM enquiries WHERE id=?", (eid,))
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/manager/export.csv")
@login_required
def export_csv():
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["ID", "Date (IST)", "Name", "Phone", "Email", "Project Type", "Location", "Budget", "Message", "Status"])
    for r in fetch():
        w.writerow([r["id"], r["ist"], r["name"], r["phone"], r["email"], r["project_type"],
                    r["location"], r["budget"], r["message"], r["status"]])
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=enquiries.csv"})


@app.route("/manager/settings", methods=["GET", "POST"])
@login_required
def manager_settings():
    m, error = get_manager(), None
    if request.method == "POST":
        check_csrf()
        f = request.form
        new_user = f.get("new_username", "").strip()
        new_pw, confirm = f.get("new_password", ""), f.get("confirm_password", "")
        if not check_password_hash(m["password_hash"], f.get("current_password", "")):
            error = "Current password is incorrect."
        elif new_user and not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", new_user):
            error = "Username must be 3-30 characters: letters, numbers, . _ - only."
        elif new_pw and len(new_pw) < 8:
            error = "New password must be at least 8 characters."
        elif new_pw != confirm:
            error = "New password and confirm password do not match."
        elif not new_pw and (not new_user or new_user == m["username"]):
            error = "Nothing to change. Enter a new username or a new password."
        else:
            with db() as c:
                c.execute("UPDATE manager SET username=?, password_hash=? WHERE id=1",
                          (new_user or m["username"], generate_password_hash(new_pw) if new_pw else m["password_hash"]))
            session.clear(); session["manager"] = True; session.permanent = True  # stay logged in with a fresh session
            return redirect(url_for("manager_settings", saved=1))
    return render_template("manager_settings.html", error=error, username=m["username"], saved=request.args.get("saved"))


init_db()
if __name__ == "__main__":
    app.run(debug=True)