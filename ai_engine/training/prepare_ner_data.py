import pandas as pd
import json
from pathlib import Path

DATASET_PATH = "../dataset/symptom_phrases_final.csv"
OUTPUT_PATH = "../training/ner_train.json"

TEMPLATES = [
    "i have {s}",
    "i am suffering from {s}",
    "i feel {s}",
    "pain related to {s}",
    "symptoms of {s}",
    "severe {s}",
    "mild {s}",
    "{s} since yesterday",
    "{s} for two days",
    "constant {s}"
]


def create_ner_data():
    df = pd.read_csv(DATASET_PATH)

    training_data = []

    for _, row in df.iterrows():
        symptom = row["symptom"].replace("_", " ").lower()

        for template in TEMPLATES:
            text = template.format(s=symptom)

            start = text.find(symptom)
            end = start + len(symptom)

            training_data.append({
                "text": text,
                "entities": [
                    {
                        "start": start,
                        "end": end,
                        "label": "SYMPTOM"
                    }
                ]
            })

    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2)

    print(f"✅ Expanded NER training data created")
    print(f"Total samples: {len(training_data)}")


if __name__ == "__main__":
    create_ner_data()
