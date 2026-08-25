import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# 1. Load environment variables from the hidden .env file
load_dotenv()

# 2. Initialize the Flask application
app = Flask(__name__)

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
@app.route("/ask", methods=["POST"])
def ask():
    """
    Receives user prompts sent as JSON from the frontend, sends them to 
    the ChatGPT API, and returns the AI's reply back to the browser.
    """
    # Extract the JSON payload sent by the browser's fetch request
    data = request.get_json()
    
    # Retrieve model, fallback to gpt-4o-mini
    selected_model = data.get("model", "gpt-4o-mini").strip()
    if not selected_model:
        selected_model = "gpt-4o-mini"

    # Validation: Reject request if the model is not on the whitelist
    if selected_model not in ALLOWED_MODELS:
        return jsonify({"error": f"Model '{selected_model}' is not authorized."}), 400

    # Retrieve conversation history list
    messages = data.get("messages", [])

    # Guard clause: Return an HTTP 400 (Bad Request) if the history is empty
    if not messages:
        return jsonify({"error": "Conversation history cannot be empty."}), 400

    try:
        # Prepend system prompt to the conversation thread
        api_messages = [
            {
                "role": "system",
                "content": "You are a helpful, concise AI assistant."
            }
        ] + messages

        # Send the conversation thread to the OpenAI Chat Completions API
        response = client.chat.completions.create(
            model=selected_model,
            messages=api_messages
        )

        # Extract the text content from the API response object
        ai_reply = response.choices[0].message.content

        # Send the answer back to the frontend as a JSON response (HTTP 200 OK)
        return jsonify({"reply": ai_reply})

    except Exception as e:
        # Catch unexpected API errors (e.g., invalid key, rate limits)
        # Return an HTTP 500 (Internal Server Error) with the error message
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True automatically reloads the server when you save code changes
    # and displays detailed tracebacks in your terminal if errors occur.
    app.run(debug=True, port=5000)