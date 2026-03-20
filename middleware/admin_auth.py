from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from database.mongo import db

users = db.users

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get("x-user-id")

        if not user_id:
            return jsonify({"message": "Unauthorized"}), 401

        user = users.find_one({"_id": ObjectId(user_id)})

        if not user or user.get("role") != "admin":
            return jsonify({"message": "Admin access only"}), 403

        return f(*args, **kwargs)

    return decorated
