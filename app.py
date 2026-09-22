from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import ollama

app = Flask(__name__)

app.secret_key = "wayvo-secret-key-change-later"

DATABASE = "wayvo.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."})

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."})

    conn = get_db()

    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        conn.close()
        return jsonify({"success": False, "message": "Account already exists."})

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

    user_message = request.json["message"]

    messages = [
        {
            "role": "system",
            "content": """You are WAYVO, a friendly, helpful, and natural AI assistant.
Speak in simple, clear language.
Be conversational and warm, not robotic.
Keep answers concise unless the user asks for details."""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )

    assistant_message = response["message"]["content"]

    return jsonify({
        "success": True,
        "response": assistant_message
    })


if __name__ == "__main__":
    app.run(debug=True)
