import logging
import os
import random

import telegram
import redis

from enum import IntEnum

from dotenv import load_dotenv
from functools import partial
from telegram import Update
from telegram.ext import Filters
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Updater

from parse_file import create_parsed_description


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('Logger')
data_base = redis.Redis(
    host='localhost',
    port=6379, db=0,
    decode_responses=True
    )


class UserStates(IntEnum):
    START_CHOICE = 1
    NEW_QUESTION_CHOICE = 2
    USERS_ANSWER = 3


def create_tg_keyboard_markup(
        buttons_text: list,
        buttons_per_row: int = 2,
        need_start: bool = False
) -> telegram.ReplyKeyboardMarkup:
    keyboard_buttons = [telegram.KeyboardButton(text) for text in buttons_text]

    rows = [
        keyboard_buttons[i:i + buttons_per_row] for i in
        range(0, len(keyboard_buttons), buttons_per_row)
    ]
    if need_start:
        rows.append([telegram.KeyboardButton('Стартовое меню')])

    return telegram.ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def start(update: Update, context: CallbackContext, title):
    user = update.effective_user
    update.message.reply_text(
        text=f'Здравствуйте, {user.full_name}!'
             f' Тема сегодняшней игры: {title}.',
        reply_markup=create_tg_keyboard_markup(
            ['Новый вопрос', 'Сдаться', 'Посмотреть счёт']
            )
    )
    return UserStates.NEW_QUESTION_CHOICE


def cancel(update, _):
    update.message.reply_text(
        'Спасибо за уделенное Вами время. '
        'Если хотите начать заново, введите команду: '
        '/start',
        reply_markup=telegram.ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_question(update: Update, context: CallbackContext, quiz_dict, title):
    user = update.effective_user
    random_task = random.choice(quiz_dict[title])
    question, answer = random_task.values()
    pipe = data_base.pipeline()
    pipe.set(user.id, question)
    pipe.set(question, answer[0])
    pipe.execute()
    update.message.reply_text(
        text=question,
        reply_markup=create_tg_keyboard_markup(
            ['Сдаться', 'Закончить игру']
            )
        )
    return UserStates.USERS_ANSWER


def handle_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text
    if user_answer in data_base.get(data_base.get(update.effective_chat.id)):
        update.message.reply_text(
            text="Ответ - верный",
            reply_markup=create_tg_keyboard_markup(
                ['Новый вопрос', 'Закончить игру']
                )
            )
        return UserStates.NEW_QUESTION_CHOICE
    else:
        update.message.reply_markdown_v2(
            'Попробуйте снова',
            reply_markup=create_tg_keyboard_markup(
                ['Сдаться', 'Закончить игру']
            )
        )
        return UserStates.USERS_ANSWER


def quit_the_game(update: Update, context: CallbackContext, quiz_dict, title):
    user = update.effective_user.id
    answer = data_base.get(data_base.get(update.effective_user.id))
    random_task = random.choice(quiz_dict[title])
    question, new_answer = random_task.values()
    pipe = data_base.pipeline()
    pipe.set(user, question)
    pipe.set(question, new_answer[0])
    pipe.execute()
    update.message.reply_text(
        text=f'Ответ: {answer}. Ваш новый вопрос: {question}',
        reply_markup=create_tg_keyboard_markup(
            ['Сдаться', 'Закончить игру']
            )
        )
    return UserStates.USERS_ANSWER


def telegram_bot(token, quiz_dict, title):
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    conversation = ConversationHandler(
        entry_points=[CommandHandler(
            'start',
            partial(start, title=title)
            )
        ],
        states={
            UserStates.NEW_QUESTION_CHOICE: [
                MessageHandler(
                    Filters.text('Новый вопрос'),
                    partial(
                        handle_question,
                        quiz_dict=quiz_dict,
                        title=title
                        )
                ),
                MessageHandler(
                    Filters.text('Сдаться'),
                    cancel
                    ),
                MessageHandler(
                    Filters.text('Закончить игру'),
                    cancel
                    )
            ],
            UserStates.USERS_ANSWER: [
                MessageHandler(
                    Filters.text("Сдаться"),
                    partial(
                        quit_the_game,
                        quiz_dict=quiz_dict,
                        title=title
                        )
                    ),
                MessageHandler(
                    Filters.text("Закончить игру"),
                    cancel
                    ),
                MessageHandler(
                    Filters.text,
                    handle_answer,
                    pass_user_data=True
                    ),
                CommandHandler(
                    'start',
                    start
                    )
            ],
        },
        fallbacks=[
            CommandHandler(
                'cancel',
                cancel
                ),
            MessageHandler(
                Filters.text('отмена'),
                cancel
                ),
            ]
    )
    dispatcher.add_handler(conversation)
    updater.start_polling()
    updater.idle()


def main():
    load_dotenv()
    tg_bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    file_name = os.environ['FILE_NAME']
    quiz_dict, title = create_parsed_description(file_name)
    telegram_bot(tg_bot_token, quiz_dict, title)


if __name__ == '__main__':
    main()
