import os
import requests
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
SYSTEM_PROMPT = (
    "Ты Рунотокс — умный ИИ-ассистент внутри проекта runotoks. "
    "Отвечай чётко, понятно и по делу на языке пользователя."
)

ALLOWED_ORIGINS = {
    "https://rya33056827-cmyk.github.io",
    "https://6827-cmyk.github.io",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "bot": "runotoks"})


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return make_response("", 204)

    if not API_KEY:
        return jsonify({"error": "Не задан GEMINI_API_KEY на сервере"}), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not user_message:
        return jsonify({"error": "Пустое сообщение"}), 400

    contents = []
    for item in history:
        role = "model" if item.get("role") == "model" else "user"
        txt = (item.get("text") or "").strip()
        if txt:
            contents.append({"role": role, "parts": [{"text": txt}]})
    if not contents or contents[-1].get("parts", [{}])[0].get("text") != user_message:
        contents.append({"role": "user", "parts": [{"text": user_message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
    }

    try:
        resp = requests.post(url, json=payload, timeout=25)
        resp.raise_for_status()
        result = resp.json()
        reply = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
        return jsonify({"reply": reply or "Не удалось сформировать ответ."})
    except requests.RequestException as exc:
        return jsonify({"error": f"Ошибка обращения к модели: {exc}"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
