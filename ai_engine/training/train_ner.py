import json
from datasets import Dataset

from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer
)

MODEL_NAME = "distilbert-base-uncased"
DATA_PATH = "../training/ner_train.json"
OUTPUT_DIR = "../ner_model"

LABEL_LIST = ["O", "B-SYMPTOM", "I-SYMPTOM"]
LABEL2ID = {l: i for i, l in enumerate(LABEL_LIST)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# ===============================
# Load dataset
# ===============================
with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)


def tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=64,
        return_offsets_mapping=True
    )

    labels = []

    for i, offsets in enumerate(tokenized_inputs["offset_mapping"]):
        label_ids = [-100] * len(offsets)
        entity = examples["entities"][i][0]

        for idx, (start, end) in enumerate(offsets):
            if start >= entity["start"] and end <= entity["end"]:
                if start == entity["start"]:
                    label_ids[idx] = LABEL2ID["B-SYMPTOM"]
                else:
                    label_ids[idx] = LABEL2ID["I-SYMPTOM"]

        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    tokenized_inputs.pop("offset_mapping")

    return tokenized_inputs


dataset = Dataset.from_list(raw_data)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

tokenized_dataset = dataset.map(
    lambda x: tokenize_and_align_labels(x, tokenizer),
    batched=True
)

model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABEL_LIST),
    id2label=ID2LABEL,
    label2id=LABEL2ID
)

training_args = TrainingArguments(
    output_dir="../ner_model",
    overwrite_output_dir=True,

    num_train_epochs=5,
    per_device_train_batch_size=8,

    logging_steps=50,
    save_steps=1000000,   
    save_total_limit=1,

    report_to="none"
)


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer
)

trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("✅ NER model trained and saved successfully")
