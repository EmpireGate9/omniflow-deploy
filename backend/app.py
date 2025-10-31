import os, io, json, base64, mimetypes
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
import csv
try:
    import openpyxl
except:
    openpyxl = None

load_dotenv()

TEXT_MODEL   = "gpt-4.1-mini"
VISION_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Load domain analyzers if exist (for your system)
DOMAIN_ANALYZERS = {}
try:
    import importlib
    BASE = Path(__file__).parent
    PLUGINS = BASE / "plugins"
    for p in PLUGINS.glob("*.py"):
        if p.name.startswith("_"): continue
        mod = importlib.import_module(f"plugins.{p.stem}")
        if hasattr(mod, "DOMAIN_CODE") and hasattr(mod, "analyze"):
            DOMAIN_ANALYZERS[mod.DOMAIN_CODE] = mod.analyze
except:
    DOMAIN_ANALYZERS = {}

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return jsonify({"ok": True, "service": "omniflow", "endpoint": "/api/analyze"})

# -------- File Extractors --------
def extract_pdf(file):
    r = PdfReader(file.stream)
    return "\n".join((p.extract_text() or "") for p in r.pages)

def extract_docx(file):
    data = file.read()
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)

def extract_csv(file):
    txt = file.read().decode("utf-8", errors="ignore")
    return list(csv.DictReader(io.StringIO(txt)))

def extract_xlsx(file):
    if not openpyxl: return {"error": "xlsx unsupported on server"}
    data = file.read()
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    out = {}
    for s in wb.sheetnames:
        ws = wb[s]
        head = None
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                head = [str(x) if x else "" for x in row]
                continue
            rows.append({ head[j]: (row[j]) for j in range(len(head))})
        out[s] = rows[:150]
    return out

# -------- AI helpers --------
def ai_text(msg):
    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful and knowledgeable AI assistant."},
            {"role": "user", "content": msg}
        ]
    )
    return resp.choices[0].message.content

def ai_vision(file, prompt):
    b64 = base64.b64encode(file.read()).decode()
    mime = file.mimetype or "image/jpeg"
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role":"system", "content":"You are a vision assistant."},
            {"role":"user","content":[
                {"type":"text","text": prompt or "حلل الصورة"},
                {"type":"image_url","image_url":{"url": f"data:{mime};base64,{b64}"}}
            ]}
        ]
    )
    return resp.choices[0].message.content

# -------- Main unified endpoint --------
@app.post("/api/analyze")
def analyze():
    if not client:
        return jsonify({"error": "missing OPENAI_API_KEY"}), 500

    content_type = request.headers.get("Content-Type", "")

    # ---------- Files Logic ----------
    if content_type.startswith("multipart/form-data"):
        f = request.files.get("file")
        user_hint = request.form.get("prompt") or ""

        if not f:
            return jsonify({"error":"no file"}), 400

        mt = f.mimetype.lower()

        # Images
        if mt.startswith("image/"):
            reply = ai_vision(f, user_hint)
            return jsonify({"kind": "image", "reply": reply})

        # PDF
        if f.filename.endswith(".pdf"):
            text = extract_pdf(f)[:8000]
            reply = ai_text(f"{user_hint or 'حلل هذا الملف'}:\n{text}")
            return jsonify({"kind": "pdf", "reply": reply})

        # DOCX
        if f.filename.endswith(".docx"):
            text = extract_docx(f)[:8000]
            reply = ai_text(f"{user_hint or 'حلل هذا المستند'}:\n{text}")
            return jsonify({"kind": "docx", "reply": reply})

        # CSV
        if f.filename.endswith(".csv"):
            rows = extract_csv(f)[:200]
            reply = ai_text(f"حلل البيانات التالية:\n{rows}")
            return jsonify({"kind": "csv", "reply": reply, "rows": len(rows)})

        # XLSX
        if f.filename.endswith(".xlsx"):
            data = extract_xlsx(f)
            reply = ai_text(f"حلل البيانات التالية:\n{str(data)[:8000]}")
            return jsonify({"kind": "xlsx", "reply": reply})

        return jsonify({"error":"unsupported file"}), 400

    # ---------- JSON / Chat Logic ----------
    data = request.json or {}
    domain = data.get("domain")
    payload = data.get("payload")

    # If it's plain text → Chat mode
    if isinstance(payload, str):
        text = payload.strip()
        try:
            json.loads(text)
        except:
            reply = ai_text(text)
            return jsonify({"result": reply})

    # JSON with domain → Domain analyzer
    if isinstance(payload, dict) and domain in DOMAIN_ANALYZERS:
        result = DOMAIN_ANALYZERS[domain](payload)
        return jsonify(result)

    # JSON without domain → summarize/interpret
    if isinstance(payload, dict):
        reply = ai_text(f"فسر هذا JSON وقدم نقاط هامة:\n{json.dumps(payload)[:8000]}")
        return jsonify({"result": reply})

    return jsonify({"error":"invalid input"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
