from flask import Blueprint, jsonify, request
from bson import ObjectId
from database.mongo import db
from services.email_service import send_email


appointments_bp = Blueprint("appointments", __name__)
appointments = db.appointments
users = db.users



# -------------------------
# GET MY APPOINTMENTS ✅ FIXED
# -------------------------
@appointments_bp.route("/my-appointments/<user_id>")
def my_appointments(user_id):
    try:
        data = list(appointments.find({
            "user_id": ObjectId(user_id)
        }))

        for a in data:
            a["_id"] = str(a["_id"])
            a["user_id"] = str(a["user_id"])
            a["doctor_id"] = str(a["doctor_id"])

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# UPDATE APPOINTMENT
# -------------------------
@appointments_bp.route("/appointments/<appointment_id>", methods=["PUT"])
def update_appointment(appointment_id):
    data = request.json

    appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {
            "date": data.get("date"),
            "time": data.get("time")
        }}
    )

    return jsonify({"message": "Appointment updated"})


# -------------------------
# DELETE APPOINTMENT
# -------------------------
@appointments_bp.route("/appointments/<appointment_id>", methods=["DELETE"])
def delete_appointment(appointment_id):
    try:
        appointment = appointments.find_one(
            {"_id": ObjectId(appointment_id)}
        )

        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        # 🔍 Fetch user email using user_id
        user = users.find_one(
            {"_id": appointment["user_id"]}
        )

        user_email = user.get("email") if user else None

        # ❌ Delete appointment
        appointments.delete_one(
            {"_id": ObjectId(appointment_id)}
        )

        # 📩 Send email only if email exists
        if user_email:
            send_email(
                to_email=user_email,
                subject="Appointment Cancelled ❌",
                body=f"""
Your appointment has been cancelled.

👨‍⚕️ Doctor: {appointment['doctor_name']}
📅 Date: {appointment['date']}
⏰ Time: {appointment['time']}

You can rebook anytime.
"""
            )
        else:
            print("⚠️ Email not found, skipping mail")

        return jsonify({"message": "Appointment deleted"})

    except Exception as e:
        print("❌ Delete error:", e)
        return jsonify({"error": str(e)}), 500

