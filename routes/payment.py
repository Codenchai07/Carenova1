import os
import hmac
import hashlib
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import razorpay
from bson import ObjectId
from database.mongo import db
from services.email_service import send_email
from database.mongo import users


load_dotenv()

payment_bp = Blueprint("payment", __name__)
appointments = db.appointments

razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

# ---------------- CREATE ORDER ----------------


@payment_bp.route("/create-order", methods=["POST"])
def create_order():
    data = request.json
    amount = data["amount"]

    order = razorpay_client.order.create({
        "amount": amount * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": "INR",
        "key": os.getenv("RAZORPAY_KEY_ID")
    })


# -------- VERIFY PAYMENT + SAVE APPOINTMENT -----
@payment_bp.route("/verify-payment", methods=["POST"])
def verify_payment():
    try:
        data = request.json
        print("📦 VERIFY DATA:", data)

        # 1️⃣ Verify signature
        payload = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
        expected_signature = hmac.new(
            os.getenv("RAZORPAY_KEY_SECRET").encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if expected_signature != data["razorpay_signature"]:
            return jsonify({"success": False, "message": "Invalid signature"}), 400

        # 2️⃣ SAVE APPOINTMENT (THIS LINE WAS BROKEN BEFORE)
        appointment = {
            "user_id": ObjectId(data["user_id"]),  # ✅ FIXED
            "doctor_id": ObjectId(data["doctor_id"]),
            "doctor_name": data["doctor_name"],
            "date": data["date"],
            "time": data["time"],
            "amount": data["amount"],
            "payment_id": data["razorpay_payment_id"],
            "order_id": data["razorpay_order_id"],
            "status": "CONFIRMED"
        }

        appointments.insert_one(appointment)
        print("✅ APPOINTMENT SAVED")
        user = users.find_one({"_id": ObjectId(data["user_id"])})

        if user:
            send_email(
        to_email=user["email"],
        subject="Appointment Confirmed ✅",
        body=f"""
Hi {user.get('name', '')},

Your appointment is CONFIRMED 🎉

Doctor: {data['doctor_name']}
Date: {data['date']}
Time: {data['time']}
Amount Paid: ₹{data['amount']}

Thank you for choosing CareNova 🩺
"""
    )


        return jsonify({"success": True})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500
