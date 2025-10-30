import os, importlib, yaml, json
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

# -------- إعدادات عامة --------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///omniflow.db")

app = Flask(__name__)
CORS(app)
engine = create_engine(DATABASE_URL, echo=False, future=True)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            kind TEXT,
            payload TEXT,
            created_at TIMESTAMP
        );
        """))
init_db()

BASE = Path(__file__).parent
PLUGINS = BASE / "plugins"
SPECS = BASE / "domain_specs"

def load_specs():
    out = {}
    for y in SPECS.glob("*.yml"):
        with open(y, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
            if d.get("code"):
                out[d["code"]] = d
    return out

def load_analyzers():
    analyzers = {}
    for p in PLUGINS.glob("*.py"):
        if p.name.startswith("_"): 
            continue
        mod = importlib.import_module(f"plugins.{p.stem}")
        if hasattr(mod, "DOMAIN_CODE") and hasattr(mod, "analyze"):
            analyzers[mod.DOMAIN_CODE] = mod.analyze
    return analyzers

DOMAIN_SPECS = load_specs()
DOMAIN_ANALYZERS = load_analyzers()

@app.get("/")
def home():
    return jsonify({
        "message":"OmniFlow Backend online",
        "endpoints":["/api/domains","/api/ingest","/api/ingest_csv?domain=...","/api/analyze","/api/artifacts"]
    })

@app.get("/api/domains")
def domains():
    return jsonify([
        {"code":k,"name":v.get("name"),"version":v.get("version"),"description":v.get("description")}
        for k,v in DOMAIN_SPECS.items()
    ])

@app.post("/api/ingest")
def ingest():
    data = request.json or {}
    domain = data.get("domain","")
    kind = data.get("kind","record")
    payload = data.get("payload",{})
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO artifacts(domain,kind,payload,created_at)
            VALUES (:d,:k,:p,:t)
        """), {
            "d": domain,
            "k": kind,
            "p": json.dumps(payload, ensure_ascii=False),
            "t": datetime.now(timezone.utc).isoformat()
        })
    return jsonify({"status":"ok"})

@app.post("/api/ingest_csv")
def ingest_csv():
    domain = request.args.get("domain","")
    if "file" not in request.files:
        return jsonify({"error":"no file"}), 400
    f = request.files["file"]
    try:
        df = pd.read_csv(f)
    except Exception as e:
        return jsonify({"error":f"bad csv: {e}"}), 400
    rows = df.to_dict(orient="records")
    with engine.begin() as conn:
        for r in rows:
            conn.execute(text("""
                INSERT INTO artifacts(domain,kind,payload,created_at)
                VALUES (:d,'record',:p,:t)
            """), {
                "d": domain,
                "p": json.dumps(r, ensure_ascii=False),
                "t": datetime.now(timezone.utc).isoformat()
            })
    return jsonify({"status":"ok","rows":len(rows)})

@app.post("/api/analyze")
def analyze():
    data = request.json or {}
    domain = data.get("domain")
    payload = data.get("payload") or {}
    if domain not in DOMAIN_ANALYZERS:
        return jsonify({"error":"unknown domain"}), 400
    try:
        result = DOMAIN_ANALYZERS[domain](payload)
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO artifacts(domain,kind,payload,created_at)
                VALUES (:d,'analysis_result',:p,:t)
            """), {
                "d": domain,
                "p": json.dumps(result, ensure_ascii=False),
                "t": datetime.now(timezone.utc).isoformat()
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.get("/api/artifacts")
def artifacts():
    # بدون pandas هنا لتبسيط الإخراج
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT id,domain,kind,payload,created_at
            FROM artifacts
            ORDER BY id DESC
        """))
        return [dict(r._mapping) for r in res]

if __name__ == "__main__":
    # نقرأ البورت الذي يوفره Render — افتراضي 8000 محليًا
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
