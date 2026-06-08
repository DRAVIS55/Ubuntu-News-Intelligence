from datasets import load_dataset
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)

print("Loading dataset...")
dataset = load_dataset("xsum", split={"train": "train[:2000]", "validation": "validation[:200]"})

MODEL = "t5-small"
print(f"Loading {MODEL}...")
tokenizer = T5Tokenizer.from_pretrained(MODEL)
model = T5ForConditionalGeneration.from_pretrained(MODEL)

MAX_INPUT  = 512
MAX_TARGET = 64

def preprocess(batch):
    inputs = ["summarize: " + doc for doc in batch["document"]]
    model_inputs = tokenizer(
        inputs, max_length=MAX_INPUT, truncation=True, padding="max_length"
    )
    labels = tokenizer(
        text_target=batch["summary"], max_length=MAX_TARGET, truncation=True, padding="max_length"
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

print("Tokenising...")
tokenised = dataset.map(preprocess, batched=True, remove_columns=dataset["train"].column_names)

args = Seq2SeqTrainingArguments(
    output_dir="./headline-model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=50,
    eval_strategy="epoch",        # fixed: was evaluation_strategy
    save_strategy="epoch",
    load_best_model_at_end=True,
    predict_with_generate=True,
    fp16=False,
    report_to="none",
)

collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

trainer = Seq2SeqTrainer(
    model=model,
    args=args,
    train_dataset=tokenised["train"],
    eval_dataset=tokenised["validation"],
    tokenizer=tokenizer,
    data_collator=collator,
)

print("\nTraining started — this will take 20–40 min on CPU. Grab chai.\n")
trainer.train()

model.save_pretrained("./headline-model/final")
tokenizer.save_pretrained("./headline-model/final")
print("\nModel saved to ./headline-model/final")