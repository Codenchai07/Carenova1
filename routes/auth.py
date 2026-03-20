from flask import Blueprint, request, jsonify, current_app
from database.mongo import users
from services.face_service import extract_embedding
from services.email_service import send_email
import bcrypt
import numpy as np
from datetime import datetime
import jwt
from datetime import datetime, timedelta
from flask import current_app


auth = Blueprint("auth", __name__)

# -------------------------------
# HELPER: COSINE SIMILARITY
# -------------------------------


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# -------------------------------
# SIGNUP
# -------------------------------
@auth.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON data"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    face = data.get("face")

    if not all([name, email, password, face]):
        return jsonify({"message": "All fields are required"}), 400

    if users.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Face embedding
    embedding = extract_embedding(face)
    if embedding is None:
        return jsonify({"message": "Face not detected"}), 400

    # Insert user
    users.insert_one({
        "name": name,
        "email": email,
        "password": hashed_pw,
        "face_embedding": embedding,
        "role": "user",              # ✅ DEFAULT ROLE
        "is_active": True,
        "created_at": datetime.utcnow()
    })

    # ✅ FIXED EMAIL CALL
    send_email(
        email,
        "Welcome to CareNova 🩺",
        f"""
Hi {name},

Welcome to CareNova!

Your account has been created successfully.
You can now:
• Login using password or face
• Book doctor appointments
• Track appointment history

Stay healthy 💙
— CareNova Team
"""
    )

    return jsonify({"message": "Signup successful!"}), 201


# -------------------------------
# LOGIN WITH PASSWORD
# -------------------------------
@auth.route("/login/password", methods=["POST"])
def login_password():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"message": "User not found"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"message": "Invalid password"}), 401

    payload = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "user"),  # 👈 default user
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "_id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user["email"],
            "role": user.get("role", "user")
        }
    }), 200


# -------------------------------
# LOGIN WITH FACE
# -------------------------------
@auth.route("/login/face", methods=["POST"])
def login_face():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON data"}), 400

        email = data.get("email")
        face = data.get("face")

        if not email or not face:
            return jsonify({"message": "Email and face data required"}), 400

        user = users.find_one({"email": email})
        if not user:
            return jsonify({"message": "User not found"}), 404

        input_embedding = extract_embedding(face)
        if input_embedding is None:
            return jsonify({"message": "Face not detected"}), 400

        stored_embedding = user.get("face_embedding")
        if stored_embedding is None:
            return jsonify({"message": "Face data missing"}), 400

        similarity = cosine_similarity(
            np.array(stored_embedding),
            np.array(input_embedding)
        )

        threshold = 0.6
        print(f"Face similarity for {email}: {similarity}")

        if similarity >= threshold:
            payload = {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "role": user.get("role", "user"),
                "exp": datetime.utcnow() + timedelta(hours=24)
            }

            token = jwt.encode(
                payload, current_app.config["SECRET_KEY"], algorithm="HS256")

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "_id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name", ""),
                "role": user.get("role", "user")
            }
        }), 200

        return jsonify({"message": "Face verification failed"}), 401

    except Exception as e:
        print("❌ Face login error:", e)
        return jsonify({"message": "Server error"}), 500
