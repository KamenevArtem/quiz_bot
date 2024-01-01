import logging
import re


logger = logging.getLogger('Logger')


def create_parsed_description():
    with open('/quiz-questions/1vs1200.txt', "r", encoding='KOI8-R') as file_content:
        quiz_description = file_content.read()
    title = quiz_description.split('\n')[1]
    quiz_dict = dict()
    quiz_dict[title] = list()
    regular_expression = r"""(Вопрос\s\d+:\n)(.*(?:\n(?!Ответ:$).*)*)
                              \n+(Ответ:$)\n
                              (.*(?:\n(?!Вопрос\s\d+:\n)|(?!Typ:\n).*)*)\n+"""
    parsed_descriptions = re.findall(
        regular_expression,
        quiz_description,
        re.VERBOSE | re.MULTILINE
        )
    for parsed_description in parsed_descriptions:
        question = parsed_description[1]
        question = " ".join(question.split('\n'))
        answer = parsed_description[3]
        answer_short = answer.split(".")[0]
        answer_full = ".".join(answer.split(".")[1:])
        quiz_dict[title].append(
            {
                'Вопрос': question,
                'Ответ': [answer_short, answer_full]
            }
        )
    return quiz_dict, title
