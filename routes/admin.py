from flask import Blueprint, jsonify
from database.mongo import db
from middleware.admin_auth import admin_required

admin_bp = Blueprint("admin", __name__)
users = db.users
appointments = db.appointments
doctors = db.doctors
payments = db.payments

@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    return jsonify({
        "users": users.count_documents({}),
        "doctors": doctors.count_documents({}),
        "appointments": appointments.count_documents({}),
        "payments": payments.count_documents({})
    })
