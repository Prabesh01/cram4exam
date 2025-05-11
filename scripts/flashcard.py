# prompt:
# from this pdf, create as much quality flash cards as you can atleast 50. make those useful for studying than redundant. give me json list of flashcards containing "front" and optionally, "back". make explainations easy to understand.
# focus on technical part / conceptual part
# used: chatgpt, claude

import json
import os
import sys

base_path = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_path)
sys.path.append(parent_dir)
db_file = os.path.join(parent_dir, 'db.sqlite3')

import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'learnquest.settings'
django.setup()
from app.models import Module, Question, User

import sqlite3
conn = sqlite3.connect(db_file)
c = conn.cursor()


modules=[
    {
        "module_code":"CC5067NP",
        "module_name": "Smart Data Discovery",
        "year_long": False,
        "year": 2,
        "semester": 2,
        "q_sem":2,
        "json_file": 'pdfs/y2/sem2/data.json'
    },
    {
        "module_code":"CS5054NP",
        "module_name": "Advanced Programming and Technologies",
        "year_long": False,
        "year": 2,
        "semester": 2,
        "q_sem":2,
        "json_file": 'pdfs/y2/sem2/apt.json'
    },
    {
        "module_code":"CS5002NP",
        "module_name": "Software Engineering",
        "year_long": True,
        "year": 2,
        "semester": 1,
        "q_sem":1,
        "json_file": 'pdfs/y2/sem1/se.json'
    },
    {
        "module_code":"CS5002NP",
        "module_name": "Software Engineering",
        "year_long": True,
        "year": 2,
        "semester": 1,
        "q_sem":2,
        "preserve": True,
        "json_file": 'pdfs/y2/sem2/se.json'
    },
]


# create bot user if not exists
user,_ = User.objects.get_or_create(
    username="bot",
    first_name="Flashcard AI",
)

for module in modules:
    module_code = module["module_code"]
    module_name = module["module_name"]
    year_long = module["year_long"]
    year = module["year"]
    semester = module["semester"]
    q_sem = module["q_sem"]
    preserve = module.get("preserve", False)

    json_file = os.path.join(base_path, module["json_file"])

    with open(json_file, 'r') as file:
        json_data = json.load(file)

    # create module if not exists
    module,_ = Module.objects.get_or_create(
        code=module_code,
        year_long=year_long,
        year=year,
        sem=semester
    )

    if not preserve:
        # delete all existing questions for the module
        Question.objects.filter(module=module,added_by=user).delete()

    # # create questions
    for item in json_data:
        question = item.get("front")
        if "back" not in item: answer = None
        else: answer = item.get("back")
        Question.objects.create(
            module=module,
            sem=q_sem,
            question=question,
            answer=answer,
            added_by=user,
            is_mcq=False,
            is_archived=False,
        )

conn.close()