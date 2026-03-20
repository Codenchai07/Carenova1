def compute_severity(symptom, base_score, followups, all_symptoms, age=None):
    score = base_score

    # Duration
    days = followups.get("duration_days")
    if days:
        days = int(days)
        if days >= 5:
            score += 3
        elif days >= 3:
            score += 2
        elif days >= 2:
            score += 1

    # Severity scale
    sev = followups.get("severity", "").lower()
    if sev == "moderate":
        score += 2
    elif sev == "severe":
        score += 4

    # Nausea fix
    if symptom == "nausea":
        if "vomiting" in all_symptoms:
            score += 3
        if "fever" in all_symptoms:
            score += 2

    # Cross symptom escalation
    if "chest_pain" in all_symptoms and "breathlessness" in all_symptoms:
        return 10, "high", "seek_immediate_care"

    # Age modifier
    if age:
        if age < 5:
            score += 2
        elif age > 60:
            score += 3

    # Final classification
    if score >= 7:
        return score, "high", "seek_immediate_care"
    elif score >= 4:
        return score, "medium", "consult_doctor"
    else:
        return score, "low", "monitor"
