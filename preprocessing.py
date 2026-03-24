import re

def clean_text(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    return text