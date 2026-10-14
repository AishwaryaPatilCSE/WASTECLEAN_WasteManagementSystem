from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "wasteclean.db"

app = Flask(__name__)
app.secret_key = "wasteclean-demo-secret-change-for-production"

# ---------------- AI PRIORITY ENGINE ----------------
TRAIN_TEXTS = [
    "small paper waste in bin", "few dry leaves near park", "plastic bottle near roadside",
    "small household garbage", "mixed waste beside road", "garbage bag near residential area",
    "overflowing bin with mixed garbage", "large garbage pile near market", "heavy waste accumulation on road",
    "open dumping and foul smell", "hazardous waste and sharp material", "medical waste dumped near public area",
    "burning garbage and smoke", "massive overflowing garbage pile"
]
TRAIN_LABELS = ["LOW","LOW","LOW","LOW","MEDIUM","MEDIUM","HIGH","HIGH","HIGH","HIGH","CRITICAL","CRITICAL","CRITICAL","CRITICAL"]
if SKLEARN_OK:
    _vectorizer = TfidfVectorizer(ngram_range=(1,2), lowercase=True)
    _model = LogisticRegression(max_iter=1000, random_state=42)
    _model.fit(_vectorizer.fit_transform(TRAIN_TEXTS), TRAIN_LABELS)
else:
    _vectorizer = _model = None

def ai_analyse(description, waste_type, report_count=0):
    text = f"{waste_type} {description}".lower()
    if SKLEARN_OK:
        pred = _model.predict(_vectorizer.transform([text]))[0]
        probs = _model.predict_proba(_vectorizer.transform([text]))[0]
        confidence = round(float(max(probs)) * 100, 1)
    else:
        confidence, pred = 70.0, "LOW"
        if any(w in text for w in ["medical", "hazardous", "burning", "chemical", "sharp"]): pred = "CRITICAL"
        elif any(w in text for w in ["overflow", "massive", "large pile", "foul smell", "dumping"]): pred = "HIGH"
        elif any(w in text for w in ["mixed", "garbage pile", "roadside"]): pred = "MEDIUM"
    if report_count >= 5 and pred == "LOW": pred = "MEDIUM"
    if report_count >= 8 and pred in ("LOW", "MEDIUM"): pred = "HIGH"
    reasons = []
    if any(w in text for w in ["overflow", "pile", "dump"]): reasons.append("accumulation/dumping detected")
    if report_count >= 5: reasons.append("recurring location")
    if any(w in text for w in ["medical", "hazardous", "burning", "chemical"]): reasons.append("potential safety risk")
    if not reasons: reasons.append("normal waste report")
    return pred, confidence, "; ".join(reasons)

# ---------------- DATABASE ----------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, citizen_id INTEGER, waste_type TEXT NOT NULL,
        description TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
        priority TEXT NOT NULL, ai_confidence REAL NOT NULL, ai_reason TEXT,
        status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL,
        FOREIGN KEY(citizen_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL, collector_id INTEGER,
        deadline TEXT, status TEXT NOT NULL DEFAULT 'Assigned', assigned_at TEXT NOT NULL,
        FOREIGN KEY(report_id) REFERENCES reports(id), FOREIGN KEY(collector_id) REFERENCES users(id)
    );
    """)
    users = [
        ("Citizen User", "citizen@wasteclean.demo", "demo123", "Citizen"),
        ("Supervisor User", "supervisor@wasteclean.demo", "demo123", "Supervisor"),
        ("Collector User 1", "collector@wasteclean.demo", "demo123", "Collector"),
        ("Admin User", "admin@wasteclean.demo", "demo123", "Admin"),
        ("Collector User 2", "neha.collector@wasteclean.demo", "demo123", "Collector"),
    ]
    for u in users:
        conn.execute("INSERT OR IGNORE INTO users(name,email,password,role) VALUES (?,?,?,?)", u)
    count = conn.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"]
    if count == 0:
        citizen_id = conn.execute("SELECT id FROM users WHERE email='citizen@wasteclean.demo'").fetchone()["id"]
        seed = [
            ("Mixed Waste", "Overflowing garbage pile near market with foul smell", 18.5208, 73.8567, "HIGH", 93.2, "accumulation/dumping detected", "Resolved", "2026-09-28 09:20"),
            ("Plastic", "Plastic bottles and bags near public park", 18.5230, 73.8490, "MEDIUM", 88.4, "normal waste report", "Collected", "2026-09-29 10:10"),
            ("Organic", "Large waste pile beside residential road", 18.5155, 73.8620, "HIGH", 91.6, "accumulation/dumping detected", "Pending", "2026-10-01 08:35"),
            ("Medical", "Potential medical waste and sharp material", 18.5280, 73.8420, "CRITICAL", 98.1, "potential safety risk", "Pending", "2026-10-02 12:45"),
            ("Mixed Waste", "Small household garbage near bus stop", 18.5100, 73.8505, "LOW", 79.2, "normal waste report", "Collected", "2026-10-02 16:20"),
            ("Mixed Waste", "Recurring dumping observed near market", 18.5208, 73.8567, "HIGH", 95.0, "recurring location", "Pending", "2026-10-03 09:05"),
            ("Plastic", "Overflowing bin near school entrance", 18.5250, 73.8550, "HIGH", 94.0, "accumulation/dumping detected", "Pending", "2026-10-04 07:50"),
            ("Other", "Dry leaves around community garden", 18.5180, 73.8460, "LOW", 82.0, "normal waste report", "Collected", "2026-10-04 14:30"),
        ]
        for r in seed:
            conn.execute("""INSERT INTO reports(citizen_id,waste_type,description,latitude,longitude,priority,ai_confidence,ai_reason,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", (citizen_id,)+r)
        # Demo operational assignments
        collector1 = conn.execute("SELECT id FROM users WHERE email='collector@wasteclean.demo'").fetchone()["id"]
        collector2 = conn.execute("SELECT id FROM users WHERE email='neha.collector@wasteclean.demo'").fetchone()["id"]
        report_ids = conn.execute("SELECT id FROM reports ORDER BY id").fetchall()
        assignments = [(report_ids[2]["id"], collector1, "2026-10-05 17:00", "Assigned"),
                       (report_ids[3]["id"], collector2, "2026-10-05 15:00", "In Progress"),
                       (report_ids[6]["id"], collector1, "2026-10-05 18:00", "Assigned")]
        for rid, cid, deadline, status in assignments:
            conn.execute("INSERT INTO tasks(report_id,collector_id,deadline,status,assigned_at) VALUES (?,?,?,?,?)",
                         (rid,cid,deadline,status,"2026-10-05 09:00"))
    conn.commit(); conn.close()

init_db()

# ---------------- HELPERS ----------------
def logged_in(): return session.get("user_id") is not None

def current_user():
    if not logged_in(): return None
    conn=db(); u=conn.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)).fetchone(); conn.close(); return u

def stats():
    conn=db()
    total=conn.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"]
    pending=conn.execute("SELECT COUNT(*) c FROM reports WHERE status IN ('Pending','Assigned')").fetchone()["c"]
    resolved=conn.execute("SELECT COUNT(*) c FROM reports WHERE status IN ('Resolved','Collected')").fetchone()["c"]
    critical=conn.execute("SELECT COUNT(*) c FROM reports WHERE priority='CRITICAL'").fetchone()["c"]
    tasks=conn.execute("SELECT COUNT(*) c FROM tasks").fetchone()["c"]
    active=conn.execute("SELECT COUNT(*) c FROM tasks WHERE status!='Completed'").fetchone()["c"]
    collectors=conn.execute("SELECT COUNT(*) c FROM users WHERE role='Collector'").fetchone()["c"]
    citizens=conn.execute("SELECT COUNT(*) c FROM users WHERE role='Citizen'").fetchone()["c"]
    conn.close()
    return {"total":total,"pending":pending,"resolved":resolved,"critical":critical,"tasks":tasks,"active":active,"collectors":collectors,"citizens":citizens,"sla":round((resolved/total)*100) if total else 0}

def role_required(*roles):
    u=current_user()
    return u and u["role"] in roles

@app.context_processor
def inject():
    return {"user":current_user(),"app_name":"WASTECLEAN","stats":stats() if logged_in() else {}}

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return redirect(url_for("dashboard")) if logged_in() else render_template("landing.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        conn=db(); u=conn.execute("SELECT * FROM users WHERE lower(email)=? AND password=?",(email,password)).fetchone(); conn.close()
        if u:
            session["user_id"]=u["id"]
            flash(f"Welcome back, {u['name'].split()[0]}. Your {u['role'].lower()} workspace is ready.","success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials. Please use a demo account.","danger")
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not logged_in(): return redirect(url_for("login"))
    role=current_user()["role"]
    conn=db(); s=stats()
    if role=="Citizen":
        reports=conn.execute("SELECT * FROM reports WHERE citizen_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
        return render_template("citizen_dashboard.html", reports=reports)
    if role=="Collector":
        tasks=conn.execute("""SELECT t.*,r.waste_type,r.description,r.latitude,r.longitude,r.priority,r.status report_status
            FROM tasks t JOIN reports r ON r.id=t.report_id WHERE t.collector_id=? ORDER BY CASE r.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,t.id DESC""",(session["user_id"],)).fetchall()
        return render_template("collector_dashboard.html", tasks=tasks)
    if role=="Supervisor":
        pending=conn.execute("""SELECT r.*,u.name citizen_name,t.id task_id,t.status task_status,cu.name collector_name
            FROM reports r LEFT JOIN users u ON u.id=r.citizen_id LEFT JOIN tasks t ON t.report_id=r.id LEFT JOIN users cu ON cu.id=t.collector_id
            WHERE r.status IN ('Pending','Assigned') ORDER BY CASE r.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,r.id DESC LIMIT 10""").fetchall()
        collectors=conn.execute("SELECT id,name,email FROM users WHERE role='Collector' ORDER BY name").fetchall()
        return render_template("supervisor_dashboard.html", pending=pending, collectors=collectors)
    recent=conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 8").fetchall()
    users=conn.execute("SELECT role,COUNT(*) c FROM users GROUP BY role ORDER BY role").fetchall()
    return render_template("admin_dashboard.html", recent=recent, users=users)

@app.route("/report", methods=["GET","POST"])
def report():
    if not logged_in(): return redirect(url_for("login"))
    if current_user()["role"] != "Citizen":
        flash("Only Citizen Portal users can submit waste reports.","danger"); return redirect(url_for("dashboard"))
    if request.method=="POST":
        waste_type=request.form.get("waste_type","Other"); description=request.form.get("description","").strip()
        lat=float(request.form.get("latitude","18.5208")); lng=float(request.form.get("longitude","73.8567"))
        conn=db(); nearby=conn.execute("SELECT COUNT(*) c FROM reports WHERE ABS(latitude-?)<0.003 AND ABS(longitude-?)<0.003",(lat,lng)).fetchone()["c"]
        priority,confidence,reason=ai_analyse(description,waste_type,nearby)
        now=datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute("""INSERT INTO reports(citizen_id,waste_type,description,latitude,longitude,priority,ai_confidence,ai_reason,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",(session["user_id"],waste_type,description,lat,lng,priority,confidence,reason,"Pending",now))
        conn.commit(); conn.close()
        flash(f"Report #{'new'} submitted. AI priority: {priority} ({confidence}% confidence).","success")
        return redirect(url_for("dashboard"))
    return render_template("report.html")

@app.route("/reports")
def reports():
    if not logged_in(): return redirect(url_for("login"))
    u=current_user()
    if u["role"] not in ("Citizen","Supervisor","Admin"):
        flash("Reports are not part of the Collector Portal.","danger"); return redirect(url_for("dashboard"))
    conn=db()
    if u["role"]=="Citizen":
        rows=conn.execute("SELECT * FROM reports WHERE citizen_id=? ORDER BY id DESC",(u["id"],)).fetchall()
        collectors=[]
    else:
        rows=conn.execute("""SELECT r.*,u.name citizen_name,t.id task_id,cu.name collector_name,t.status task_status
            FROM reports r LEFT JOIN users u ON u.id=r.citizen_id LEFT JOIN tasks t ON t.report_id=r.id LEFT JOIN users cu ON cu.id=t.collector_id
            ORDER BY CASE r.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,r.id DESC""").fetchall()
        collectors=conn.execute("SELECT id,name FROM users WHERE role='Collector' ORDER BY name").fetchall()
    conn.close(); return render_template("reports.html",reports=rows,collectors=collectors)

@app.route("/assign/<int:report_id>",methods=["POST"])
def assign(report_id):
    if not role_required("Supervisor","Admin"):
        flash("Only supervisors or admins can assign collection tasks.","danger"); return redirect(url_for("dashboard"))
    collector_id=request.form.get("collector_id"); deadline=request.form.get("deadline")
    conn=db(); existing=conn.execute("SELECT id FROM tasks WHERE report_id=?",(report_id,)).fetchone()
    if existing: conn.execute("UPDATE tasks SET collector_id=?,deadline=?,status='Assigned' WHERE report_id=?",(collector_id,deadline,report_id))
    else: conn.execute("INSERT INTO tasks(report_id,collector_id,deadline,status,assigned_at) VALUES (?,?,?,?,?)",(report_id,collector_id,deadline,"Assigned",datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.execute("UPDATE reports SET status='Assigned' WHERE id=?",(report_id,)); conn.commit(); conn.close()
    flash("Collection task assigned and added to the collector workspace.","success"); return redirect(url_for("dashboard"))

@app.route("/tasks")
def tasks():
    if not logged_in(): return redirect(url_for("login"))
    u=current_user()
    if u["role"] not in ("Collector","Supervisor","Admin"):
        flash("Task management is not part of the Citizen Portal.","danger"); return redirect(url_for("dashboard"))
    conn=db()
    if u["role"]=="Collector":
        rows=conn.execute("""SELECT t.*,r.waste_type,r.description,r.latitude,r.longitude,r.priority,u.name collector_name
            FROM tasks t JOIN reports r ON r.id=t.report_id LEFT JOIN users u ON u.id=t.collector_id WHERE t.collector_id=? ORDER BY CASE r.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,t.id DESC""",(u["id"],)).fetchall()
    else:
        rows=conn.execute("""SELECT t.*,r.waste_type,r.description,r.latitude,r.longitude,r.priority,u.name collector_name
            FROM tasks t JOIN reports r ON r.id=t.report_id LEFT JOIN users u ON u.id=t.collector_id ORDER BY CASE r.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,t.id DESC""").fetchall()
    conn.close(); return render_template("tasks.html",tasks=rows)

@app.route("/task/<int:task_id>/status",methods=["POST"])
def task_status(task_id):
    if not logged_in(): return redirect(url_for("login"))
    u=current_user(); new_status=request.form.get("status","In Progress"); conn=db()
    task=conn.execute("SELECT report_id,collector_id FROM tasks WHERE id=?",(task_id,)).fetchone()
    if not task or (u["role"]=="Collector" and task["collector_id"]!=u["id"]):
        conn.close(); flash("You are not authorized to update this task.","danger"); return redirect(url_for("tasks"))
    conn.execute("UPDATE tasks SET status=? WHERE id=?",(new_status,task_id))
    report_status="Collected" if new_status=="Completed" else "Assigned"
    conn.execute("UPDATE reports SET status=? WHERE id=?",(report_status,task["report_id"]))
    conn.commit(); conn.close(); flash(f"Task #{task_id} moved to {new_status}.","success"); return redirect(url_for("tasks"))

@app.route("/analytics")
def analytics():
    if not logged_in(): return redirect(url_for("login"))
    if current_user()["role"] not in ("Supervisor","Admin"):
        flash("Analytics are available to Supervisor and Administrator Portals.","danger"); return redirect(url_for("dashboard"))
    conn=db(); priority=conn.execute("SELECT priority,COUNT(*) c FROM reports GROUP BY priority").fetchall(); waste=conn.execute("SELECT waste_type,COUNT(*) c FROM reports GROUP BY waste_type ORDER BY c DESC").fetchall(); hotspots=conn.execute("SELECT ROUND(latitude,3) lat,ROUND(longitude,3) lng,COUNT(*) c FROM reports GROUP BY ROUND(latitude,3),ROUND(longitude,3) HAVING c>=2 ORDER BY c DESC").fetchall(); conn.close()
    return render_template("analytics.html",priority=priority,waste=waste,hotspots=hotspots)

@app.route("/admin")
def admin():
    if not role_required("Admin"):
        flash("Admin access only.","danger"); return redirect(url_for("dashboard"))
    conn=db(); users=conn.execute("SELECT id,name,email,role FROM users ORDER BY role,name").fetchall(); recent=conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10").fetchall(); conn.close()
    return render_template("admin_dashboard.html",recent=recent,users=users,full_admin=True)

@app.route("/api/reports")
def api_reports():
    conn=db(); rows=conn.execute("SELECT id,waste_type,description,latitude,longitude,priority,status,ai_confidence,created_at FROM reports ORDER BY id DESC").fetchall(); conn.close(); return jsonify([dict(r) for r in rows])

@app.route("/reset-demo",methods=["POST"])
def reset_demo():
    if not role_required("Admin"):
        flash("Only an admin can reset demo data.","danger"); return redirect(url_for("dashboard"))
    conn=db(); conn.execute("DELETE FROM tasks"); conn.execute("DELETE FROM reports"); conn.commit(); conn.close(); init_db(); flash("Demo data restored with role-specific sample tasks.","success"); return redirect(url_for("dashboard"))

if __name__=="__main__":
    print("\nWASTECLEAN running at http://127.0.0.1:5000")
    app.run(debug=True)
