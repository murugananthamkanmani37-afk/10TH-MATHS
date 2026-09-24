import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import ERROR_MESSAGE, GENERATION_SETTINGS, SYSTEM_PROMPT

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite"
MAX_MESSAGE_LENGTH = 1000
MAX_HISTORY_ITEMS = 20

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_contents(history, message):
    contents = []

    for item in history[-MAX_HISTORY_ITEMS:]:
        role = item.get("role")
        text = str(item.get("text", "")).strip()
        if role in ("user", "model") and text:
            contents.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )

    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please type a message."}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(
            {"error": f"Messages can be up to {MAX_MESSAGE_LENGTH} characters."}
        ), 400

    if not isinstance(history, list):
        history = []

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                **GENERATION_SETTINGS,
            ),
        )
        reply = (response.text or "").strip() or ERROR_MESSAGE
        return jsonify({"reply": reply})
    except Exception:
        return jsonify({"error": ERROR_MESSAGE}), 500


if __name__ == "__main__":
    app.run(debug=True)
