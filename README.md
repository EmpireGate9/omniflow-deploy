# OmniFlow — Full Deploy (Local + Render)

## تشغيل محليًا
### Backend
```bash
cd backend
python -m venv .venv
# ويندوز: .venv\Scripts\activate | ماك/لينكس: source .venv/bin/activate
pip install -r requirements.txt
python app.py
# API على: http://127.0.0.1:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# افتح http://localhost:5173
```

## النشر على Render (Blueprint)
1) ارفع هذا المجلد إلى GitHub (repo الخاص بك).
2) افتح Render.com → New + → Blueprint → اختر هذا الريبو (يحتوي render.yaml).
3) سينشئ Render خدمتين: Backend وFrontend ويضبط `VITE_BACKEND_URL` تلقائيًا.
4) بعد البناء، ستحصل على رابط الواجهة + رابط الـAPI.

> لإضافة مجالات تحليل جديدة: أضف ملفًا في `backend/plugins/` وملف spec في `backend/domain_specs/` ثم ادفع التغييرات.
