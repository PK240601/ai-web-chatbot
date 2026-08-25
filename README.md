# AI Web Chatbot

A clean, responsive web chat application powered by Python, Flask, Tailwind CSS, and OpenAI's API.

🚀 **Live Demo:** [https://ai-web-chatbot-pt32.onrender.com/](https://ai-web-chatbot-pt32.onrender.com/)

---

## Overview

This application provides a modern browser-based interface for interacting with Large Language Models. The frontend sends asynchronous JSON requests to a local Flask backend, which manages credentials securely and interfaces with OpenAI's `gpt-4o-mini` model.

---

## Tech Stack

* **Backend:** Python 3, Flask
* **AI Model:** OpenAI API (`gpt-4o-mini`)
* **Frontend:** HTML5, Tailwind CSS, JavaScript (Fetch API)
* **Configuration:** `python-dotenv` for secure environment variable management

---

## Project Structure

```text
ai-web-chatbot/
├── templates/
│   └── index.html      # Responsive frontend interface
├── .env                # API keys & secrets (git-ignored)
├── .gitignore          # Excludes venv, keys, and cache files
├── app.py              # Flask server and API endpoints
├── README.md           # Project documentation
└── requirements.txt    # Project dependencies
```

---

## Getting Started

### 1. Prerequisites
* Python 3.9 or higher
* OpenAI API Key

### 2. Clone the Repository
```bash
git clone https://github.com/PK240601/ai-web-chatbot.git
cd ai-web-chatbot
```

### 3. Set Up Virtual Environment
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. Launch the App
```bash
python app.py
```

Navigate to `http://127.0.0.1:5000` in your web browser to start chatting.

---

## License
Distributed under the MIT License.
