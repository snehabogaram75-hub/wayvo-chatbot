from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from google import genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DATABASE = "wayvo.db"

gemini_client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        })

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        })

    conn = get_db()

    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        conn.close()
        return jsonify({
            "success": False,
            "message": "Account already exists."
        })

    hashed_password = generate_password_hash(password)

    conn.execute(
        "INSERT INTO users (email, password) VALUES (?, ?)",
        (email, hashed_password)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully!"
    })


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email", "").strip()
    password = data.get("password", "")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "Account not found."
        })

    if not check_password_hash(user["password"], password):
        return jsonify({
            "success": False,
            "message": "Incorrect password."
        })

    session["user_id"] = user["id"]
    session["email"] = user["email"]

    return jsonify({
        "success": True,
        "message": "Login successful!"
    })


@app.route("/chat-page")
def chat_page():
    if "user_id" not in session:
        return render_template("index.html")

    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    user_message = request.json.get("message", "").strip()

    if not user_message:
        return jsonify({
            "success": False,
            "message": "Please enter a message."
        })

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_message,
            config={
                "system_instruction": """You are WAYVO, a friendly, helpful, and natural AI assistant.
Speak in simple, clear language.
Be conversational and warm, not robotic.
Keep answers concise unless the user asks for details."""
            }
        )

        assistant_message = response.text

        return jsonify({
            "success": True,
            "response": assistant_message
        })

       except Exception as e:
        print("GEMINI ERROR:", repr(e))
        return jsonify({
            "success": False,
            "message": "WAYVO could not connect to the AI service."
        }), 500



if __name__ == "__main__":
    app.run(debug=True)
