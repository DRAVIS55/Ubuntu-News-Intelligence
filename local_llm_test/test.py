from transformers import T5Tokenizer, T5ForConditionalGeneration

model = T5ForConditionalGeneration.from_pretrained("./headline-model/final")
tokenizer = T5Tokenizer.from_pretrained("./headline-model/final")

def generate_headline(article_text):
    input_text = "summarize: " + article_text
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(
        inputs["input_ids"],
        max_length=64,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test with a Kenyan news article
article = """
The Central Bank of Kenya has raised the base lending rate by 50 basis points
to 13 percent, citing persistent inflationary pressure driven by fuel costs and
a weakening shilling. Governor Kamau Thugge said the move was necessary to
anchor inflation expectations and protect the value of the Kenyan currency.
The decision was unanimous among the Monetary Policy Committee members.
Economists warn the rate hike may slow credit growth and hurt small businesses
already struggling with high operating costs.
"""

headline = generate_headline(article)
print(f"Generated headline:\n{headline}")