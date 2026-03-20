import pandas as pd
import re
from sentence_transformers import SentenceTransformer, util


class SymptomDetector:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        df = pd.read_csv(
            "ai_engine/dataset/symptom_phrases_final.csv"
        )

        self.phrases = df["phrase"].str.lower().tolist()
        self.symptoms = df["symptom"].tolist()
        self.embeddings = self.model.encode(
            self.phrases, convert_to_tensor=True
        )

        self.phrase_tokens = [
            set(re.findall(r"[a-z]+", p)) for p in self.phrases
        ]

        self.vomiting_keywords = {
            "vomit", "vomiting", "puke", "puking", "throw", "threw"
        }

        # 🔹 NORMALIZATION MAP (SAFE)
        self.token_aliases = {
            "breathless": "breath",
            "breathlessness": "breath",
            "breathing": "breath",
            "chestpain": "chest pain",
            "stomachache": "stomach ache",
            "headache": "head pain"
        }

    def normalize_text(self, text):
        text = text.lower()
        for k, v in self.token_aliases.items():
            text = text.replace(k, v)
        return text

    def detect_symptoms(self, text, threshold=0.62, max_symptoms=3):
        text = self.normalize_text(text)

        text_tokens = set(re.findall(r"[a-z]+", text))

        query_emb = self.model.encode(text, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, self.embeddings)[0]

        matches = []

        for i, score in enumerate(scores):
            score_val = float(score)

            if score_val < threshold:
                continue

            if not (self.phrase_tokens[i] & text_tokens):
                continue

            symptom = self.symptoms[i]

            if symptom == "vomiting" and not (self.vomiting_keywords & text_tokens):
                continue

            matches.append((symptom, score_val))

        matches.sort(key=lambda x: x[1], reverse=True)

        detected = []
        for symptom, _ in matches:
            if symptom not in detected:
                detected.append(symptom)
            if len(detected) >= max_symptoms:
                break

        return detected
