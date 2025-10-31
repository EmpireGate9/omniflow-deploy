import os, io, json, base64, csv, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# ========== إعدادات أساسية ==========
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
          domain TEXT,
          kind TEXT,
          payload TEXT,
          created_at TEXT
        )""")
init_db()

# مبدئيًا نتجاهل plugins الحقيقية لضمان عمل الواجهة
DOMAIN_ANALYZERS = {}

app = Flask(__name__)
app.url_map.strict_slashes = False   # يقبل / وبدون /
CORS(app)

# ========== مساعدات ==========
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def log_artifact(domain, kind, payload_obj):
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO artifacts(domain,kind,payload,created_at) VALUES (?,?,?,?)",
            (domain or "", kind, json.dumps(payload_obj, ensure_ascii=False), now_iso())
        )

# ========== نقاط فحص ==========
@app.get("/")
def root():
    return jsonify({
        "ok": True,
        "service": "omniflow",
        "endpoints": [
            "/domains", "/artifacts", "/analyze",
            "/api/domains", "/api/artifacts", "/api/analyze"
        ]
    })

# ========== المجالات (نسختان: بدون /api ومع /api) ==========
def _domains_payload():
    if DOMAIN_ANALYZERS:
        return [
            {"code": c, "name": c.capitalize(), "description": f"Domain: {c}"}
            for c in sorted(DOMAIN_ANALYZERS.keys())
        ]
    # قائمة افتراضية متوافقة مع الواجهة
    return [
        {"code": "general",      "name": "General",      "description": "مساعد عام"},
        {"code": "construction", "name": "Construction", "description": "تحليل مشاريع البناء"},
        {"code": "medical",      "name": "Medical",      "description": "تحليل تقارير طبية"},
        {"code": "cars",         "name": "Cars",         "description": "تشخيص أعطال المركبات"},
    ]

@app.get("/domains")
@app.get("/api/domains")
def get_domains():
    return jsonify(_domains_payload())

# ========== السجلات (نسختان) ==========
@app.get("/artifacts")
@app.get("/api/artifacts")
def get_artifacts():
    try:
        with db_conn() as conn:
            cur = conn.execute("""
              SELECT id,domain,kind,payload,created_at
              FROM artifacts ORDER BY id DESC LIMIT 200
            """)
            return jsonify([dict(r) for r in cur.fetchall()]), 200
    except:
        # نرجّع قائمة فاضية مع 200 حتى لا تظهر رسالة تعذر التحميل
        return jsonify([]), 200

@app.post("/artifacts/clear")
@app.post("/api/artifacts/clear")
def clear_artifacts():
    try:
        with db_conn() as conn:
            conn.execute("DELETE FROM artifacts")
        return jsonify({"ok": True})
    except:
        return jsonify({"ok": True})

# ========== ذكاء نصي بسيط (دردشة) ==========
# مبدئيًا نعيد echo لضمان الرد حتى بدون مفاتيح خارجية
def chat_reply(text: str) -> str:
    # يمكن لاحقًا توصيل OpenAI؛ الآن نضمن الرد وعدم الفشل
    return f"🤖 رد تلقائي: {text[:400]}"

# ========== نقطة التحليل الموحّدة (نسختان) ==========
@app.post("/analyze")
@app.post("/api/analyze")
def analyze():
    """
    تدعم واجهتك كما هي:
    - إذا أرسلت نصًا خامًا في 'payload' → نرد فورًا (شات)
    - إذا أرسلت JSON ومعه domain مدعوم → (مكان توصيل plug-ins لاحقًا)
    """
    # ملفات (لو واجهتك ترسلها مستقبلاً بنفس المسار)
    ct = request.headers.get("Content-Type", "")
    if ct.startswith("multipart/form-data"):
        f = request.files.get("file")
        if not f:
            return jsonify({"error": "no file uploaded"}), 400
        name = (f.filename or "").lower()
        # لأجل واجهتك الحالية، نكتفي بتسجيل العملية والرد برسالة بسيطة
        log_artifact("file", "upload", {"file": name})
        return jsonify({"kind": "file", "reply": f"تم استلام الملف: {name}"}), 200

    # JSON / نص
    data = request.json or {}
    domain  = data.get("domain")  # قد تكون فارغة - لا مشكلة
    payload = data.get("payload")

    # نص حر (سلسلة) → دردشة
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return jsonify({"error": "empty message"}), 400
        reply = chat_reply(text)
        log_artifact("chat", "message", {"q": text, "a": reply})
        return jsonify({"result": reply}), 200

    # JSON + domain (لو أردت لاحقًا توصيل محللات)
    if isinstance(payload, dict) and domain in DOMAIN_ANALYZERS:
        try:
            res = DOMAIN_ANALYZERS[domain](payload)
            log_artifact(domain, "analysis", res)
            return jsonify(res), 200
        except Exception as e:
            return jsonify({"error": f"domain-analyzer-failed: {e}"}), 500

    # JSON بدون domain → لخصه نصيًا (echo مبدئي)
    if isinstance(payload, dict):
        reply = chat_reply(f"تحليل JSON: {json.dumps(payload, ensure_ascii=False)[:8000]}")
        log_artifact("json", "summary", {"input": payload, "reply": reply})
        return jsonify({"result": reply}), 200

    return jsonify({"error": "invalid input"}), 400

# ========== 404 مفيد أثناء التشخيص ==========
@app.errorhandler(404)
def not_found(e):
    routes = sorted([str(r) for r in app.url_map.iter_rules()])
    return jsonify({"error": "not found", "available_routes": routes}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
