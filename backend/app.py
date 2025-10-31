import os, io, json, base64, csv, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

load_dotenv()

TEXT_MODEL = "gpt-4.1-mini"
VISION_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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
          )
        """)
init_db()

def log_artifact(domain, kind, payload_obj):
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO artifacts(domain,kind,payload,created_at) VALUES (?,?,?,?)",
            (domain or "", kind, json.dumps(payload_obj, ensure_ascii=False),
             datetime.now(timezone.utc).isoformat())
        )

# محاولة تحميل Plugins إن وُجدت
DOMAIN_ANALYZERS = {}
try:
    import importlib
    PLUGINS = BASE / "plugins"
    for p in PLUGINS.glob("*.py"):
        if p.name.startswith("_"): continue
        mod = importlib.import_module(f"plugins.{p.stem}")
        if hasattr(mod, "DOMAIN_CODE") and hasattr(mod, "analyze"):
            DOMAIN_ANALYZERS[mod.DOMAIN_CODE] = mod.analyze
except Exception:
    DOMAIN_ANALYZERS = {}

app = Flask(__name__)
app.url_map.strict_slashes = False  # ← قبول / وبدون /
CORS(app)

# ---------- مساعدو ذكاء ----------
def ai_text(msg:str)->str:
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role":"system","content":"You are a helpful assistant."},
            {"role":"user","content":msg}
        ]
    )
    return resp.choices[0].message.content

def ai_vision(file, prompt:str)->str:
    file.stream.seek(0)
    b64 = base64.b64encode(file.read()).decode("utf-8")
    mime = file.mimetype or "image/jpeg"
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role":"system","content":"You are a vision assistant."},
            {"role":"user","content":[
                {"type":"text","text": prompt or "حلل الصورة وأعطني المطلوب"},
                {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}}
            ]}
        ]
    )
    return resp.choices[0].message.content

# ---------- Extractors ----------
def extract_pdf(fs): 
    r = PdfReader(fs.stream); return "\n".join((p.extract_text() or "") for p in r.pages)
def extract_docx(fs):
    data = fs.read(); doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
def extract_csv(fs):
    txt = fs.read().decode("utf-8", errors="ignore")
    return list(csv.DictReader(io.StringIO(txt)))
def extract_xlsx(fs):
    try:
        import openpyxl
    except Exception:
        return {"error":"openpyxl غير متوفر"}
    data = fs.read(); wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out = {}
    for s in wb.sheetnames:
        ws = wb[s]; rows=[]; headers=None
        for i,row in enumerate(ws.iter_rows(values_only=True)):
            if i==0: headers=[str(x) if x is not None else "" for x in row]; continue
            rows.append({headers[j] if j<len(headers) else f"col{j}": (row[j] if j<len(row) else None)
                         for j in range(len(headers))})
        out[s]=rows[:200]
    return out

# ---------- Routes ----------
@app.get("/")
@app.get("/api")
def root():
    return jsonify({"ok":True,"service":"omniflow","endpoints":["/api/domains","/api/artifacts","/api/analyze"]})

@app.get("/api/domains")
def get_domains():
    if DOMAIN_ANALYZERS:
        return jsonify([{"code":c,"name":c.capitalize(),"description":f"Domain: {c}"} for c in sorted(DOMAIN_ANALYZERS.keys())])
    # قائمة افتراضية متوافقة مع الواجهة
    return jsonify([
        {"code":"general","name":"General","description":"مساعد عام"},
        {"code":"construction","name":"Construction","description":"تحليل مشاريع البناء"},
        {"code":"medical","name":"Medical","description":"تحليل تقارير طبية"},
        {"code":"cars","name":"Cars","description":"تشخيص أعطال المركبات"},
    ])

@app.get("/api/artifacts")
def get_artifacts():
    with db_conn() as conn:
        cur = conn.execute("SELECT id,domain,kind,payload,created_at FROM artifacts ORDER BY id DESC LIMIT 200")
        return jsonify([dict(r) for r in cur.fetchall()])

@app.post("/api/analyze")
def analyze():
    if client is None:
        return jsonify({"error":"OPENAI_API_KEY is missing"}), 500

    ct = request.headers.get("Content-Type","")
    hint = request.form.get("prompt") or ""

    # ملفات
    if ct.startswith("multipart/form-data"):
        f = request.files.get("file")
        if not f: return jsonify({"error":"no file uploaded"}),400
        name = (f.filename or "").lower()

        if f.mimetype.startswith("image/"):
            reply = ai_vision(f, hint); log_artifact("vision","image",{"file":name,"reply":reply})
            return jsonify({"kind":"image","reply":reply})

        if name.endswith(".pdf"):
            text = extract_pdf(f)[:8000]; reply = ai_text(f"{hint or 'حلل هذا الملف'}:\n{text}")
            log_artifact("pdf","doc",{"file":name,"reply":reply}); return jsonify({"kind":"pdf","reply":reply})

        if name.endswith(".docx"):
            text = extract_docx(f)[:8000]; reply = ai_text(f"{hint or 'حلل هذا المستند'}:\n{text}")
            log_artifact("docx","doc",{"file":name,"reply":reply}); return jsonify({"kind":"docx","reply":reply})

        if name.endswith(".csv"):
            rows = extract_csv(f)[:200]; reply = ai_text(f"حلّل البيانات التالية:\n{rows}")
            log_artifact("csv","table",{"file":name,"rows":len(rows),"reply":reply}); return jsonify({"kind":"csv","reply":reply})

        if name.endswith(".xlsx"):
            tbl = extract_xlsx(f); reply = ai_text(f"حلّل البيانات:\n{json.dumps(tbl,ensure_ascii=False)[:8000]}")
            log_artifact("xlsx","table",{"file":name,"reply":reply}); return jsonify({"kind":"xlsx","reply":reply})

        return jsonify({"error":"unsupported file"}),400

    # JSON/نص
    data = request.json or {}
    domain = data.get("domain")
    payload = data.get("payload")

    # نص حر
    if isinstance(payload,str):
        txt = payload.strip()
        try:
            payload = json.loads(txt)  # لو كان JSON كنص
        except Exception:
            reply = ai_text(txt); log_artifact("chat","message",{"q":txt,"a":reply})
            return jsonify({"result":reply})

    # JSON + domain (إن وُجد محلل)
    if isinstance(payload,dict) and domain in DOMAIN_ANALYZERS:
        try:
            res = DOMAIN_ANALYZERS[domain](payload); log_artifact(domain,"analysis",res)
            return jsonify(res)
        except Exception as e:
            return jsonify({"error":f"domain-analyzer-failed: {e}"}),500

    # JSON بدون domain → تحليل عام
    if isinstance(payload,dict):
        reply = ai_text(f"حلّل هذا JSON وقدّم نقاط مهمة:\n{json.dumps(payload,ensure_ascii=False)[:8000]}")
        log_artifact("json","summary",{"input":payload,"reply":reply})
        return jsonify({"result":reply})

    return jsonify({"error":"invalid input"}),400

if __name__ == "__main__":
    port = int(os.environ.get("PORT",8000))
    app.run(host="0.0.0.0", port=port)
