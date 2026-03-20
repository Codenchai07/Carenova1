from flask import Blueprint, request, jsonify
from services.email_service import send_contact_notification_to_admin

contact_bp = Blueprint("contact", __name__, url_prefix="/api/contact")


@contact_bp.route("/submit", methods=["POST"])
def submit_contact():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email or not message:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    send_contact_notification_to_admin(name, email, message)

    return jsonify({
        "success": True,
        "message": "Message sent successfully"
    }), 200
