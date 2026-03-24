SKILLS = [
    "python", "java", "sql",
    "machine learning", "data analysis",
    "excel", "deep learning"
]

def extract_skills(text):
    found_skills = []
    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill)
    return found_skills