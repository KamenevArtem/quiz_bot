import random
import os

import redis

from dotenv import load_dotenv

import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from parse_file import create_parsed_description


def handle_new_question(event, vk_api, data_base, quiz_dict, title, keyboard):
    random_task = random.choice(quiz_dict[title])
    question, answer = random_task.values()
    pipe = data_base.pipeline()
    pipe.set(event.user_id, question)
    pipe.set(question, answer[0])
    pipe.execute()
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
        )


def handle_surrender(event, vk_api):
    vk_api.messages.send(
                user_id=event.user_id,
                message='Спасибо за уделенное Вами время. '
                'Если хотите начать заново, введите команду: '
                '"Начать" или "Заново"',
                random_id=random.randint(1, 1000),
                )


def handle_correct_answer(event, vk_api, keyboard):
    vk_api.messages.send(
                user_id=event.user_id,
                message="Правильно",
                random_id=random.randint(1, 1000),
                keyboard=keyboard.get_keyboard()
                )


def handle_start(event, vk_api, keyboard):
    vk_api.messages.send(
                user_id=event.user_id,
                message='Здравствуйте! Выберете, что Вас интересует.',
                random_id=random.randint(1, 1000),
                keyboard=keyboard.get_keyboard()
                )


def handle_unknown(event, vk_api):
    vk_api.messages.send(
                user_id=event.user_id,
                message='Неверный ответ. Если Вам не был выслан вопрос,'
                ' напишите "Начать" или "Заново"',
                random_id=random.randint(1, 1000),
                )


def launch_vk_bot(vk_token, quiz_dict, title):
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    data_base = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
        )
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Посмотреть счёт', color=VkKeyboardColor.PRIMARY)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Новый вопрос":
                handle_new_question(
                    event,
                    vk_api,
                    data_base,
                    quiz_dict,
                    title,
                    keyboard
                    )
            elif event.text == "Сдаться":
                handle_surrender(event, vk_api)
            elif event.text in data_base.get(data_base.get(event.user_id)):
                handle_correct_answer(event, vk_api, keyboard)
            elif event.text in ["Начать", "Заново"]:
                handle_start(event, vk_api, keyboard)
            else:
                handle_unknown(event, vk_api)


def main():
    load_dotenv()
    file_name = os.environ['FILE_NAME']
    vk_token = os.environ['VK_API_KEY']
    quiz_dict, title = create_parsed_description(file_name)
    launch_vk_bot(vk_token, quiz_dict, title)


if __name__ == "__main__":
    main()
