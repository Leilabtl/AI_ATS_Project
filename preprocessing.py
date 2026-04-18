import re

def clean_text(text):
    text = text.lower()
    text = text.replace("\n", " ")
    # Keep characters common in technical skills: . / # +
    text = re.sub(r'[^a-zA-Z0-9 ./#+]', '', text)
    return text.strip()