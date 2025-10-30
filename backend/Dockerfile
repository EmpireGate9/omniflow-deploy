# ==== Backend Dockerfile (Render) ====
FROM python:3.11-slim

WORKDIR /app

# منع إنشاء .pyc وتسريب البافر
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات الباكند
COPY . .

# Render يضبط env PORT تلقائيًا – نحن نقرأه داخل app.py
EXPOSE 8000

# شغّل Flask مباشرة ليستخدم PORT من الـ env
CMD ["python", "app.py"]
