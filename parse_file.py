import collections
import os
import re


def create_parsed_description(questions_file_path):
    with open(
            questions_file_path,
            "r",
            encoding='KOI8-R') as file_content:
        quiz_description = file_content.read()
    title = quiz_description.split('\n')[1]
    quiz_dict = {}
    regular_expression = r"""(Вопрос\s\d+:\n)(.*(?:\n(?!Ответ:$).*)*)
                              \n+(Ответ:$)\n
                              (.*(?:\n(?!Вопрос\s\d+:\n)|(?!Typ:\n).*)*)\n+"""
    parsed_descriptions = re.findall(
        regular_expression,
        quiz_description,
        re.VERBOSE | re.MULTILINE
        )
    for parsed_description in parsed_descriptions:
        parsed_description = tuple(
            description for description in parsed_description
            if description != "Ответ:"
            )
        question_number, question, answer = parsed_description
        question = " ".join(question.split('\n'))
        answer_short = answer.split(".")[0]
        answer_full = ".".join(answer.split(".")[1:])
        quiz_dict.setdefault(title, []).append(
            {
                'Вопрос': question,
                'Ответ': [answer_short, answer_full]
            }
        )
    return quiz_dict, title
