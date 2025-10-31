from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# تخزين مؤقت داخل الذاكرة
conversation_history = []
domains = [
    {"id": "general", "name": "مساعد عام"},
    {"id": "medical", "name": "الطب"},
    {"id": "engineering", "name": "الهندسة"},
    {"id": "contracts", "name": "المقاولات"},
    {"id": "cars", "name": "السيارات"},
]

@app.route("/", methods=["GET"])
def home():
    return "OmniFlow API Running ✅"

@app.route("/api/domains", methods=["GET"])
def get_domains():
    return jsonify(domains)

@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify(conversation_history)

@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    conversation_history.clear()
    return jsonify({"success": True})

@app.route("/api/chat", methods=["POST"])
def chat():
    user_input = request.json.get("question", "")
    domain = request.json.get("domain", "general")

    if not user_input:
        return jsonify({"error": "no question provided"}), 400

    # رد مؤقت (سيتم استبداله بذكاء حقيقي لاحقًا)
    response = f"🔧 ({domain}) – ميزة الذكاء قيد التوصيل.\n\nسؤالك: {user_input}"

    # تخزين السجل
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    conversation_history.append({
        "role": "assistant",
        "content": response
    })

    return jsonify({"answer": response})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
