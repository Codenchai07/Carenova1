from flask import Blueprint, request, jsonify
from bson import ObjectId
from database.mongo import db
import os
from werkzeug.utils import secure_filename

users_bp = Blueprint("users", __name__)
users = db.users

UPLOAD_FOLDER = "uploads/profiles"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------
# GET USER PROFILE
# -------------------------


@users_bp.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    user = users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return jsonify({"message": "User not found"}), 404

    user["_id"] = str(user["_id"])
    return jsonify(user)


# -------------------------
# UPDATE USER PROFILE + IMAGE
# -------------------------
@users_bp.route("/user/<user_id>", methods=["PUT"])
def update_user(user_id):
    name = request.form.get("name")
    age = request.form.get("age")
    gender = request.form.get("gender")

    update_fields = {
        "name": name,
        "age": age,
        "gender": gender
    }

    # IMAGE HANDLING (ADDED)
    if "profile_image" in request.files:
        file = request.files["profile_image"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            update_fields["profile_image"] = f"/uploads/profiles/{filename}"

    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )

    updated_user = users.find_one(
        {"_id": ObjectId(user_id)}, {"password": 0}
    )
    updated_user["_id"] = str(updated_user["_id"])

    return jsonify(updated_user)


# -------------------------
# DELETE USER
# -------------------------
@users_bp.route("/user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    users.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"message": "User deleted successfully"})
