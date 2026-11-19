import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables from the hidden .env file
load_dotenv()

# 2. Initialize the Flask application
app = Flask(__name__)

# Trust one proxy hop (Render) so request.remote_addr is the real client IP,
# not the load balancer's - otherwise every user would share one rate limit.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# Per-IP rate limiting so nobody can drain the OpenAI credit.
# Uses in-memory storage (per gunicorn worker); set RATELIMIT_STORAGE_URI
# to a Redis URL for a shared limit across workers.
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

# Limits on what the browser can send
MAX_HISTORY = 20            # only the last N messages are sent to the model
MAX_MESSAGE_CHARS = 8000    # per-message length cap

# 3. Initialize the OpenAI client using your API key from the environment
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------------------------------------------------------------------------
# ROUTE 1: Serves the main HTML webpage
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """
    When a user visits http://127.0.0.1:5000 in their browser,
    Flask looks inside the 'templates' folder and serves 'index.html'.
    """
    return render_template("index.html")

# Whitelist of authorized models to prevent parameter injection
ALLOWED_MODELS = {
    "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5-mini", "gpt-5-nano",
    "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4o-mini", "o3-mini", "o4-mini"
}

# ---------------------------------------------------------------------------
# ROUTE 2: API Endpoint to handle incoming user questions
# ---------------------------------------------------------------------------
@app.errorhandler(429)
def rate_limited(e):
    """Return rate-limit errors as JSON so the frontend can display them."""
    return jsonify({"error": "Too many requests. Please wait a minute and try again."}), 429


def clean_messages(raw):
    """
    Keep only well-formed user/assistant messages. This stops a client from
    injecting its own 'system' messages and caps history size (token cost).
    """
    if not isinstance(raw, list):
        return []
    cleaned = [
        {"role": m["role"], "content": m["content"][:MAX_MESSAGE_CHARS]}
        for m in raw
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
        and m["content"].strip()
    ]
    return cleaned[-MAX_HISTORY:]


@app.route("/ask", methods=["POST"])
@limiter.limit("20/minute")
def ask():
    """
    Receives the conversation as JSON, sends it to the OpenAI API with
    stream=True, and streams the reply back to the browser as plain text.
    """
    # silent=True returns None instead of raising on a missing/invalid JSON body
    data = request.get_json(silent=True) or {}

    # Retrieve model, fallback to gpt-4o-mini
    selected_model = str(data.get("model") or "gpt-4o-mini").strip()

    # Validation: Reject request if the model is not on the whitelist
    if selected_model not in ALLOWED_MODELS:
        return jsonify({"error": f"Model '{selected_model}' is not authorized."}), 400

    messages = clean_messages(data.get("messages"))

    # Guard clause: the last message must be a user message
    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "Conversation must end with a user message."}), 400

    api_messages = [
        {"role": "system", "content": "You are a helpful, concise AI assistant."}
    ] + messages

    try:
        # Open the stream before returning, so errors like a bad API key
        # still come back as a normal JSON error with a 502 status.
        stream = client.chat.completions.create(
            model=selected_model,
            messages=api_messages,
            stream=True,
        )
    except Exception:
        # Log full details server-side; don't leak them to the browser
        app.logger.exception("OpenAI request failed")
        return jsonify({"error": "The AI service is unavailable right now. Please try again."}), 502

    def generate():
        try:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception:
            app.logger.exception("OpenAI stream interrupted")
            yield "\n\n_[Response interrupted. Please try again.]_"

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain; charset=utf-8",
        # Ask proxies not to buffer, so chunks reach the browser immediately
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

# ---------------------------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True automatically reloads the server when you save code changes
    # and displays detailed tracebacks in your terminal if errors occur.
    app.run(debug=True, port=5000)