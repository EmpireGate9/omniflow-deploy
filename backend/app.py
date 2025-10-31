import os, io, json, base64, csv, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# ====== إعداد أساسي ======
BASE = Path(__file__).parent
DB_PATH = BASE / "omniflow.db"

def db_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS artifacts(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          domain TEXT, kind TEXT, payload TEXT, created_at TEXT
        )""")
init_db()

# قد توجد Plugins، نتجاهلها الآن (سنضيفها لاحقًا)
DOMAIN_ANALYZERS = {}

app = Flask(__name__)
app.url_map.strict_slashes = False   # يقبل / وبدون /
CORS(app)

# ====== نقاط فحص سريعة ======
@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
@app.get("/api")
def root():
    return jsonify({
        "ok": True,
        "service": "omniflow",
        "endpoints": ["/api/domains", "/api/artifacts", "/api/analyze", "/healthz"]
    })

# ====== المجالات بصيغة متوافقة مع الواجهة ======
@app.get("/api/domains")
def get_domains():
    if DOMAIN_ANALYZERS:
        return jsonify([
            {"code": c, "name": c.capitalize(), "description": f"Domain: {c}"}
            for c in sorted(DOMAIN_ANALYZERS.keys())
        ])
    # قائمة افتراضية حتى تختفي رسالة تعذر التحميل
    return jsonify([
        {"code": "general", "name": "General", "description": "مساعد عام"},
        {"code": "construction", "name": "Construction", "description": "تحليل مشاريع البناء"},
        {"code": "medical", "name": "Medical", "description": "تحليل تقارير طبية"},
        {"code": "cars", "name": "Cars", "description": "تشخيص أعطال المركبات"},
    ])

# ====== السجلات (فارغة بالبداية) ======
@app.get("/api/artifacts")
def get_artifacts():
    with db_conn() as conn:
        cur = conn.execute("SELECT id,domain,kind,payload,created_at FROM artifacts ORDER BY id DESC LIMIT 200")
        return jsonify([dict(r) for r in cur.fetchall()])

# ====== تحليل موحد (نص فقط مؤقتًا لنتحقق من المسارات) ======
@app.post("/api/analyze")
def analyze():
    data = request.json or {}
    payload = data.get("payload")
    domain  = data.get("domain") or "general"

    if isinstance(payload, str):
        # نعيدها كاختبار
        result = f"(echo) [{domain}] {payload.strip()}"
        # نسجل
        with db_conn() as conn:
            conn.execute(
                "INSERT INTO artifacts(domain,kind,payload,created_at) VALUES (?,?,?,?)",
                (domain, "message", json.dumps({"q": payload, "a": result}, ensure_ascii=False),
                 datetime.now(timezone.utc).isoformat())
            )
        return jsonify({"result": result})

    return jsonify({"error": "send plain text in 'payload' for now"}), 400

# ====== مُعالج 404 يظهر لك المسارات المتاحة ======
@app.errorhandler(404)
def not_found(e):
    routes = sorted([str(r) for r in app.url_map.iter_rules()])
    return jsonify({"error": "not found", "available_routes": routes}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
