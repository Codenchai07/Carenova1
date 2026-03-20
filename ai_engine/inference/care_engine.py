def get_care(symptom, care_df):
    row = care_df[care_df["symptom"] == symptom]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "home": r["home_care"],
        "medicine": r["medicine_note"],
        "doctor": r["when_to_see_doctor"]
    }


def get_precautions(symptom, level, precautions_df):
    rows = precautions_df[
        (precautions_df["symptom_id"] == symptom) &
        (precautions_df["severity_level"] == level)
    ]
    return rows["precaution_text"].tolist()
