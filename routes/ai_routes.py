from flask import Blueprint, request, jsonify
import pandas as pd
import uuid

from langdetect import detect
from deep_translator import GoogleTranslator

from ai_engine.inference.symptom_detector import SymptomDetector
from ai_engine.inference.severity_engine import compute_severity
from ai_engine.inference.care_engine import get_care, get_precautions

ai_bp = Blueprint("ai_bp", __name__)

# -----------------------------
# Load resources
# -----------------------------
detector = SymptomDetector()

followups_df = pd.read_csv("ai_engine/dataset/followup_questions.csv")
severity_df = pd.read_csv("ai_engine/dataset/severity_rules_final.csv")
care_df = pd.read_csv("ai_engine/dataset/care_guidance_extended.csv")
precautions_df = pd.read_csv("ai_engine/dataset/precautions.csv")

# -----------------------------
# In-memory session store
# -----------------------------
SESSIONS = {}
MAX_QUESTIONS = 3


# -----------------------------
# Translation helpers
# -----------------------------
def detect_language(text):
    try:
        lang = detect(text)

        # Fix wrong detection for short English inputs
        if len(text.split()) <= 3 and lang != "en":
            return "en"

        return lang
    except:
        return "en"


def translate(text, source, target):
    if source == target:
        return text
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except:
        return text


# -----------------------------
# Choose primary symptom
# -----------------------------
def choose_primary(symptoms):
    if len(symptoms) == 1:
        return symptoms[0]

    scores = {}
    for s in symptoms:
        row = severity_df[severity_df["symptom"] == s]
        scores[s] = int(row["severity_score"].values[0]
                        ) if not row.empty else 0

    return max(scores, key=scores.get)


@ai_bp.route("/ai/chat", methods=["POST"])
def chat_ui():
    data = request.json
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    # -----------------------------
    # Detect & translate user input
    # -----------------------------
    user_lang = detect_language(user_message)
    message_en = translate(user_message, user_lang, "en")

    # -----------------------------
    # Init session
    # -----------------------------
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "primary_symptom": None,
            "associated_symptoms": [],
            "questions": [],
            "answers": {},
            "index": 0,
            "lang": user_lang
        }

    session = SESSIONS[session_id]

    # =====================================================
    # PHASE 1 — SYMPTOM DETECTION
    # =====================================================
    if session["primary_symptom"] is None:
        symptoms = detector.detect_symptoms(message_en)

        if not symptoms:
            reply = "I couldn’t identify clear symptoms. Please describe them in more detail."
            return jsonify({
                "session_id": session_id,
                "reply": translate(reply, "en", user_lang)
            })

        primary = choose_primary(symptoms)
        associated = [s for s in symptoms if s != primary]

        session["primary_symptom"] = primary
        session["associated_symptoms"] = associated

        qs = followups_df[
            followups_df["symptom"] == primary
        ]["question"].dropna().unique().tolist()

        if "fever" in associated:
            qs = [q for q in qs if "fever" not in q.lower()]

        if not qs:
            qs = [
                "How long have you had this symptom?",
                "Is it getting worse over time?",
                "Does anything relieve it?"
            ]

        session["questions"] = qs[:MAX_QUESTIONS]
        session["index"] = 0
        session["answers"] = {}

        symptom_list = "\n".join(
            [f"• {s.replace('_', ' ')}" for s in symptoms]
        )

        reply = (
            "I detected the following symptoms:\n"
            f"{symptom_list}\n\n"
            f"I’ll focus on {primary.replace('_', ' ')}.\n"
            "Let me ask a few questions."
        )

        return jsonify({
            "session_id": session_id,
            "reply": translate(reply, "en", user_lang),
            "next_question": translate(session["questions"][0], "en", user_lang)
        })

    # =====================================================
    # PHASE 2 — FOLLOW-UP QUESTIONS
    # =====================================================
    idx = session["index"]
    current_question = session["questions"][idx]

    session["answers"][current_question] = message_en
    session["index"] += 1

    if session["index"] < len(session["questions"]):
        return jsonify({
            "session_id": session_id,
            "next_question": translate(
                session["questions"][session["index"]],
                "en",
                user_lang
            )
        })

    # =====================================================
    # PHASE 3 — SEVERITY + CARE
    # =====================================================
    primary = session["primary_symptom"]
    all_symptoms = [primary] + session["associated_symptoms"]

    row = severity_df[severity_df["symptom"] == primary]
    base_score = int(row["severity_score"].values[0]) if not row.empty else 0

    score, level, action = compute_severity(
        primary,
        base_score,
        session["answers"],
        all_symptoms
    )

    care = get_care(primary, care_df)
    precautions = get_precautions(primary, level, precautions_df)

    del SESSIONS[session_id]

    reply = (
        "Based on your answers, here’s my assessment.\n\n"
        f"Severity level appears to be {level}."
    )

    return jsonify({
        "session_id": session_id,
        "reply": translate(reply, "en", user_lang),
        "advice": {
            "home_care": [
                translate(care["home"], "en", user_lang)
            ] if care and care.get("home") else [],
            "medicine": [
                translate(care["medicine"], "en", user_lang)
            ] if care and care.get("medicine") else [],
            "warning": translate(
                "Please seek immediate medical attention."
                if action == "seek_immediate_care"
                else "Consult a doctor if symptoms persist.",
                "en",
                user_lang
            )
        }
    })
