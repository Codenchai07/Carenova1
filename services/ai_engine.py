import pandas as pd
import math
import json


# -----------------------------
# Load datasets
# -----------------------------
SYMPTOMS_DF = pd.read_csv("dataset/symptoms_dataset.csv")
FOLLOWUP_DF = pd.read_csv("dataset/carenova_followup_kb_1010_merged.csv")
MEDICINE_DF = pd.read_csv(
    "dataset/symptoms_medicine_recommendations_2000_optionC.csv")


# ---------------------------------------------------------
# 1) Extract symptoms from free text
# ---------------------------------------------------------
def extract_symptoms(text):
    text = text.lower()
    detected = []

    for s in SYMPTOMS_DF["symptom"].unique():
        if s.lower() in text:
            detected.append(s)

    return list(set(detected))


# ---------------------------------------------------------
# 2) Get follow-up questions based on symptoms
# ---------------------------------------------------------
def get_followup_questions(symptoms):
    questions = []

    for s in symptoms:
        row = FOLLOWUP_DF[FOLLOWUP_DF["symptom"] == s]
        if not row.empty:
            try:
                qs = json.loads(row.iloc[0]["followups"])
                questions.extend(qs)
            except:
                pass

    # Remove yes/no only questions
    filtered = []
    for q in questions:
        if "yes or no" not in q.lower():
            filtered.append(q)

    return filtered


# ---------------------------------------------------------
# 3) Severity assessment from answers
# ---------------------------------------------------------
def assess_severity_from_answers(answers):
    score = 0

    for a in answers:
        val = a["answer"].lower()

        # Numeric intensity
        if val.isdigit():
            num = int(val)
            if num >= 7:
                score += 3
            elif num >= 4:
                score += 2
            else:
                score += 1

        # Time duration
        elif "day" in val or "week" in val:
            score += 2

        # Text-based fallback
        elif any(x in val for x in ["severe", "intense", "worst"]):
            score += 3
        elif any(x in val for x in ["mild", "little"]):
            score += 1

    if score >= 7:
        return {"level": "high", "score": score}
    elif score >= 4:
        return {"level": "moderate", "score": score}
    else:
        return {"level": "low", "score": score}


# ---------------------------------------------------------
# 4) Generate recommendations
# ---------------------------------------------------------
def generate_recommendations(symptoms, severity):
    diseases = (
        SYMPTOMS_DF[SYMPTOMS_DF["symptom"].isin(symptoms)]["disease"]
        .value_counts()
    )

    if diseases.empty:
        return {"message": "No condition identified"}

    disease = diseases.index[0]
    row = MEDICINE_DF[MEDICINE_DF["disease"] == disease]

    if row.empty:
        return {"disease": disease, "advice": "Consult a doctor"}

    return {
        "disease": disease,
        "severity": severity,
        "medicines": json.loads(row.iloc[0]["medicines"]),
        "precautions": json.loads(row.iloc[0]["precautions"]),
        "note": "Consult doctor if symptoms worsen"
    }


