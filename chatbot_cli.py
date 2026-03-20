import pandas as pd
from ai_engine.inference.symptom_detector import SymptomDetector
from ai_engine.inference.severity_engine import compute_severity
from ai_engine.inference.care_engine import get_care, get_precautions

# -------------------- INIT --------------------
detector = SymptomDetector()

followups_df = pd.read_csv("ai_engine/dataset/followup_questions.csv")
severity_df = pd.read_csv("ai_engine/dataset/severity_rules_final.csv")
care_df = pd.read_csv("ai_engine/dataset/care_guidance_extended.csv")
precautions_df = pd.read_csv("ai_engine/dataset/precautions.csv")

print("🩺 Symptom Detection + Follow-up + Severity + Care Mode")
print("Type 'exit' to quit.\n")

# -------------------- CONSTANTS --------------------
BAD_SEVERITY_FRAGMENTS = {
    "is the pain mild",
    "mild",
    "moderate",
    "or severe?",
    "is the pain severe",
    "is the pain moderate"
}

SEVERITY_ALLOWED = {"nausea", "chest_pain", "headache"}
SEVERITY_QUESTION = "On a scale of mild / moderate / severe, how bad is it?"

GENERIC_QUESTIONS = [
    "How long have you had this symptom?",
    "Is it getting worse over time?",
    "Does anything relieve it?"
]

# -------------------- MAIN LOOP --------------------
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break

    symptoms = detector.detect_symptoms(user_input)
    if not symptoms:
        print("Bot: No symptoms detected.\n")
        continue

    print(f"\nBot: Detected symptoms: {symptoms}")
    collected = {}

    # -------------------- FOLLOW-UPS --------------------
    for s in symptoms:
        collected[s] = {}
        asked = set()

        qs = followups_df[
            followups_df["symptom"] == s
        ]["question"].dropna().unique().tolist()

        print(f"\n🔍 Follow-up for {s}:")

        # 1️⃣ Ask severity once if applicable
        if s in SEVERITY_ALLOWED:
            ans = input(f"Bot: {SEVERITY_QUESTION} ")
            collected[s]["severity"] = ans.lower().strip()
            asked.add(SEVERITY_QUESTION)

        # 2️⃣ Ask dataset questions
        for q in qs:
            if len(collected[s]) >= 3:
                break

            if q.lower().strip() in BAD_SEVERITY_FRAGMENTS:
                continue

            if q in asked:
                continue

            ans = input(f"Bot: {q} ")
            collected[s][q] = ans
            asked.add(q)

            if "day" in q.lower():
                digits = "".join(filter(str.isdigit, ans))
                if digits:
                    collected[s]["duration_days"] = int(digits)

        # 3️⃣ Pad to minimum 3 questions
        for g in GENERIC_QUESTIONS:
            if len(collected[s]) >= 3:
                break
            if g in asked:
                continue

            ans = input(f"Bot: {g} ")
            collected[s][g] = ans
            asked.add(g)

    # -------------------- SEVERITY + CARE --------------------
    print("\n🧠 Severity Assessment & Care Guidance\n")

    for s, data in collected.items():

        # SAFE severity base lookup
        row = severity_df[severity_df["symptom"] == s]
        base = int(row["severity_score"].values[0]) if not row.empty else 0

        score, level, action = compute_severity(
            s, base, data, symptoms
        )

        care = get_care(s, care_df)
        precautions = get_precautions(s, level, precautions_df)

        print(f"🔴 {s.upper()}")
        print(f"• Severity Score: {score}")
        print(f"• Severity Level: {level}")
        print(f"• Recommended Action: {action}")

        if care:
            if care.get("home"):
                print(f"🏠 Home Care: {care['home']}")
            if care.get("medicine"):
                print(f"💊 Medicine: {care['medicine']}")

        if precautions:
            print("⚠️ Precautions:")
            for p in precautions:
                print(f"  - {p}")

        print("\n⚠️ Disclaimer:")
        print("This is not a medical diagnosis. Please consult a doctor.\n")
