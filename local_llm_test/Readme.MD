# News Headline AI — Fine-Tuned Language Model

## What This Is

This project is a **pilot proof-of-concept** for a larger vision: an AI system that understands African news, detects patterns across time, and assists journalists with research and writing.

This pilot specifically trains a small language model to do **one focused task**:

> Given a full news article, generate a concise, accurate headline.

It is the foundation of something bigger. Once you understand how fine-tuning works here — swapping the dataset, scaling the model, and adding new task prefixes — you can extend this into:

- Historical pattern matching ("when did Kenya last see this?")
- Peer country comparison briefings
- Swahili / Sheng article summarisation
- Political trend detection across East Africa

This pilot runs entirely on your laptop. No API. No internet after setup. No ongoing cost.

---

## How It Works

The model used is **T5-small** — a 60MB open-source text-to-text transformer originally built by Google and released publicly. It is not ChatGPT. It is small enough to train on a CPU laptop in under an hour.

Fine-tuning means we take this pre-trained model (which already understands English grammar and structure) and continue training it specifically on news article → headline pairs. After training, the model has learned the pattern of how good headlines are written from article content.

The training data comes from **XSum** — a dataset of 226,000 BBC news articles each paired with a human-written one-sentence summary. We use 2,000 articles for training and 200 for validation so it finishes in reasonable time on a CPU.

```
Input  → "The Central Bank of Kenya has raised the base lending rate by 50 basis 
          points citing persistent inflationary pressure..."

Output → "Kenya central bank raises lending rate amid inflation pressure"
```

The trained model is saved to your machine and runs fully offline from that point forward.

---

## Project Structure

After cloning and running, your folder will look like this:

```
news-headline-ai/
├── train.py                  # Fine-tuning script — run this first
├── test.py                   # Inference script — run this after training
├── README.md                 # This file
├── venv/                     # Python virtual environment (created by you)
└── headline-model/
    └── final/                # Your trained model (created after training)
        ├── config.json
        ├── tokenizer.json
        └── pytorch_model.bin
```

---

## Requirements

### System

| Requirement | Minimum |
|---|---|
| OS | Ubuntu 20.04+ / Debian / any Linux |
| Python | 3.8 or higher |
| RAM | 4GB minimum, 8GB recommended |
| Disk space | ~3GB (model weights + dataset cache) |
| GPU | Not required — CPU works |
| Internet | Required during setup only |

Check your Python version:

```bash
python3 --version
```

If it is below 3.8, upgrade it first:

```bash
sudo apt update && sudo apt install python3.10 python3.10-venv -y
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dravis55/africa-news-nlp-pilot.git
cd news-headline-ai
```

### 2. Create a virtual environment

This keeps all dependencies isolated from your system Python. Always do this.

```bash
python3 -m venv venv
source venv/bin/activate
```

You will see `(venv)` appear at the start of your terminal line. That means it is active. Every time you open a new terminal session you must run `source venv/bin/activate` again before running any scripts.

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install transformers datasets torch sentencepiece accelerate
```

**What each package does:**

| Package | Purpose |
|---|---|
| `transformers` | Hugging Face library — loads and runs T5 and all modern LLMs |
| `datasets` | Hugging Face dataset library — downloads and manages training data |
| `torch` | PyTorch — the deep learning engine that runs the actual training |
| `sentencepiece` | Tokeniser used by T5 to convert text into numbers the model reads |
| `accelerate` | Hugging Face utility that optimises training on CPU or GPU |

This step downloads approximately 700MB. It will take 5–10 minutes depending on your connection. Run it once — after that everything runs offline.

---

## Training the Model

### Run the training script

```bash
python3 train.py
```

You will see output like this:

```
Loading dataset...
Loading t5-small...
Tokenising...
Training started — this will take 20–40 min on CPU. Grab chai.

{'loss': 2.34, 'learning_rate': 0.0001, 'epoch': 1.0}
{'loss': 1.87, 'learning_rate': 0.00005, 'epoch': 2.0}
{'loss': 1.61, 'learning_rate': 0.0, 'epoch': 3.0}

Model saved to ./headline-model/final
```

**What is happening during training:**

- Epoch 1–3: The model reads 2,000 article-headline pairs in batches of 4
- After each batch it calculates how wrong its headline was (the loss number)
- It adjusts its internal weights to be less wrong next time
- Loss going down (2.34 → 1.61) means the model is learning
- After 3 epochs the best version is saved to `./headline-model/final`

**Expected time on CPU:** 20–45 minutes depending on your machine.

Do not close the terminal while it is running.

---

## Testing the Model

Once training finishes, run the inference script:

```bash
python3 test.py
```

The script loads your saved model and generates a headline for a sample Kenyan news article about CBK interest rates.

Expected output:

```
Generated headline:
Kenya central bank raises lending rate amid inflation pressure
```

### Testing with your own articles

Open `test.py` and replace the `article` variable with any news article text:

```python
article = """
Paste your own article text here. The longer and more detailed
the article, the better the headline generation will be.
"""
```

Then run:

```bash
python3 test.py
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'transformers'`**

You are running Python outside the virtual environment. Run:
```bash
source venv/bin/activate
```

**`Killed` or process dies mid-training**

Your machine ran out of RAM. Reduce batch size in `train.py`:
```python
per_device_train_batch_size=2,   # change 4 to 2
per_device_eval_batch_size=2,
```

**Dataset download fails or hangs**

Check your internet connection. The XSum dataset is ~300MB and downloads from Hugging Face on first run only.

**Training is taking more than 2 hours**

Reduce the training data size in `train.py`:
```python
dataset = load_dataset("xsum", split={
    "train": "train[:500]",        # reduce from 2000 to 500
    "validation": "validation[:50]"
})
```

---

## Extending This for the Full African News AI Vision

This pilot is step one of a larger system. Here is how you grow it:

### Use African news data instead of BBC

Replace the XSum dataset with your own scraped articles from Nation Media, Standard, AllAfrica, or KNA. Format them as a CSV with two columns — `article` and `headline` — and load with:

```python
from datasets import load_dataset
dataset = load_dataset("csv", data_files={"train": "kenya_news.csv"})
```

### Add new task types

T5 is a text-to-text model — you teach it new tasks by adding a prefix:

```python
"summarize: "    # → generate headline
"compare: "      # → find historical parallel
"translate: "    # → Swahili to English
"brief: "        # → generate journalist briefing
```

Train on examples of each task and the model learns all of them.

### Upgrade to a larger model

When you have GPU access (rented cloud GPU, $1–2/hr on Vast.ai):

```python
MODEL = "google/flan-t5-base"    # 250MB, much smarter
MODEL = "google/flan-t5-large"   # 780MB, significantly stronger
```

The training code does not change — only the model name.

### Make it Swahili-aware

Use a multilingual base model instead:

```python
MODEL = "google/mt5-small"   # same size, trained on 101 languages including Swahili
```

Then fine-tune on Swahili article-headline pairs.

---

## The Bigger Picture

This pilot demonstrates that:

1. You do not need cloud APIs or OpenAI to build AI — open-source models run on your own hardware
2. Fine-tuning is not building from scratch — you are steering an existing model toward your specific task
3. Your data is your moat — the same code trained on Kenyan news data produces a model that understands Kenyan context, something no foreign API can replicate
4. The path from this pilot to a production African news intelligence system is a matter of data, compute, and iteration — not a different technology

---

## License

MIT — free to use, modify, and build on.

---

## Author

Built as a pilot for an African-native news AI platform.  
Nairobi, Kenya.