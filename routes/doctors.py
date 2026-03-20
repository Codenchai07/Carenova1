from flask import Blueprint, jsonify, request
from bson import ObjectId
from database.mongo import db

doctors_bp = Blueprint("doctors_bp", __name__)
doctors = db.doctors


# ----------------------------
# GET ALL DOCTORS
# ----------------------------
@doctors_bp.route("/doctors", methods=["GET"])
def get_doctors():
    all_doctors = list(doctors.find())
    for d in all_doctors:
        d["_id"] = str(d["_id"])
    return jsonify(all_doctors)


# ----------------------------
# SEARCH + FILTER
# ----------------------------
@doctors_bp.route("/doctors/search", methods=["GET"])
def search_doctors():
    name = request.args.get("q")
    specialization = request.args.get("specialization")

    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    if specialization:
        query["specialization"] = specialization

    results = list(doctors.find(query))
    for d in results:
        d["_id"] = str(d["_id"])

    return jsonify(results)


# ----------------------------
# GET SINGLE DOCTOR (ADDED)
# ----------------------------
@doctors_bp.route("/doctors/<doctor_id>", methods=["GET"])
def get_doctor_details(doctor_id):
    try:
        doctor = doctors.find_one({"_id": ObjectId(doctor_id)})

        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        doctor["_id"] = str(doctor["_id"])
        return jsonify(doctor)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
