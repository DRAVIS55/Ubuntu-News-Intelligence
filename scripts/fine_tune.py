"""
scripts/fine_tune.py — Fine-tune a language model on African news data

Usage:
    python scripts/fine_tune.py \\
        --base-model "google/flan-t5-base" \\
        --data data/african_news_training.jsonl \\
        --output models/anip-flan-t5 \\
        --task summarisation

Supported tasks: summarisation, headline_generation, classification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_training_data_from_archive(output_path: str, task: str = "summarisation"):
    """
    Build a JSONL training dataset from the article archive using Django ORM.
    """
    from core.models import Article
    from intelligence.llm import get_llm

    logger.info(f"Building training data for task: {task}")
    llm = get_llm()

    records = []
    articles = list(
        Article.objects
        .filter(word_count__gte=200)
        .order_by("-published_at")[:500]
    )

    logger.info(f"Processing {len(articles)} articles...")

    for i, article in enumerate(articles):
        if task == "summarisation":
            record = {
                "input": f"Summarise this African news article in 2-3 sentences:\n\n{article.body[:2000]}",
                "output": article.summary or "",
            }
            if not record["output"] and i < 50:
                try:
                    summary = llm.complete(
                        f"Summarise in 2 sentences:\n{article.body[:1500]}",
                        max_tokens=100,
                        temperature=0.2,
                    )
                    record["output"] = summary
                except Exception:
                    continue

        elif task == "headline_generation":
            record = {
                "input": f"Generate a clear, specific news headline for this East African article:\n\n{article.body[:1500]}",
                "output": article.title,
            }

        elif task == "classification":
            categories = ["politics", "business", "health", "sports", "crime", "environment"]
            category = article.category if article.category in categories else "general"
            record = {
                "input": f"Classify this African news article into one category (politics/business/health/sports/crime/environment):\n\n{article.title}\n\n{article.body[:500]}",
                "output": category,
            }
        else:
            logger.error(f"Unknown task: {task}")
            sys.exit(1)

        if record["output"]:
            records.append(record)

    with open(output_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    logger.info(f"Saved {len(records)} training records to {output_path}")
    return len(records)


def fine_tune_t5(
    base_model: str,
    data_path: str,
    output_dir: str,
    num_epochs: int = 3,
    batch_size: int = 8,
    max_input_length: int = 512,
    max_target_length: int = 128,
):
    """Fine-tune a T5/Flan-T5 model on the African news dataset."""
    try:
        from transformers import (
            T5ForConditionalGeneration,
            T5Tokenizer,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
            DataCollatorForSeq2Seq,
        )
        from datasets import Dataset
        import torch
    except ImportError:
        logger.error("Missing dependencies. Run: pip install transformers datasets torch")
        sys.exit(1)

    logger.info(f"Loading base model: {base_model}")
    tokenizer = T5Tokenizer.from_pretrained(base_model)
    model = T5ForConditionalGeneration.from_pretrained(base_model)

    data = []
    with open(data_path) as f:
        for line in f:
            data.append(json.loads(line.strip()))

    logger.info(f"Loaded {len(data)} training examples")

    split = int(len(data) * 0.9)
    train_data = data[:split]
    val_data = data[split:]

    def tokenize(examples):
        model_inputs = tokenizer(
            examples["input"],
            max_length=max_input_length,
            truncation=True,
            padding="max_length",
        )
        labels = tokenizer(
            examples["output"],
            max_length=max_target_length,
            truncation=True,
            padding="max_length",
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_dataset = Dataset.from_list(train_data).map(tokenize, batched=True)
    val_dataset = Dataset.from_list(val_data).map(tokenize, batched=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=50,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        predict_with_generate=True,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("Starting fine-tuning...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info(f"Model saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune model on African news data")
    parser.add_argument("--base-model", default="google/flan-t5-base")
    parser.add_argument("--data", default="data/african_news_training.jsonl")
    parser.add_argument("--output", default="models/anip-flan-t5")
    parser.add_argument("--task", default="headline_generation",
                        choices=["summarisation", "headline_generation", "classification"])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--build-data", action="store_true",
                        help="Build training data from the article archive first")
    args = parser.parse_args()

    if args.build_data or not os.path.exists(args.data):
        logger.info("Building training data from archive...")
        os.makedirs(os.path.dirname(args.data) if os.path.dirname(args.data) else ".", exist_ok=True)
        n = build_training_data_from_archive(args.data, task=args.task)
        logger.info(f"Training data built: {n} records")

    if not os.path.exists(args.data):
        logger.error(f"Training data not found at {args.data}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    fine_tune_t5(
        base_model=args.base_model,
        data_path=args.data,
        output_dir=args.output,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
    )

    logger.info("\nFine-tuning complete!")
    logger.info("To use your model, set in .env:")
    logger.info(f"  LLM_PROVIDER=local")
    logger.info(f"  LOCAL_MODEL_PATH={args.output}/model.gguf")


if __name__ == "__main__":
    main()
