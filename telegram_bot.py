import logging
import os
import random

import telegram
import redis

from enum import IntEnum

from dotenv import load_dotenv
from telegram import ForceReply
from telegram import Update
from telegram.ext import Filters
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Updater

from parse_file import create_parsed_description


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger('Logger')
data_base = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
quiz_dict, title = create_parsed_description()


class UserStates(IntEnum):
    START_CHOICE = 1
    NEW_QUESTION_CHOICE = 2
    USERS_ANSWER = 3
    QUIT_CHOICE = 4


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Посмотреть счёт']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                one_time_keyboard=True
                                                )
    update.message.reply_markdown_v2(
        fr'Здравствуйте, {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup,
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


def handle_question(update: Update, context: CallbackContext):
    user = update.effective_user
    random_task = random.choice(quiz_dict[title])
    question, answer = random_task.values()
    pipe = data_base.pipeline()
    pipe.set(user.id, question)
    pipe.set(question, answer[0])
    pipe.execute()
    update.message.reply_text(text=f'{question} Если Вы хотите сдаться и '
                              'перейти в начальное меню, напишите мне "Сдаться"')
    return UserStates.USERS_ANSWER


def handle_answer(update: Update, context: CallbackContext):
    user_answer = update.message.text
    if user_answer in data_base.get(data_base.get(update.effective_chat.id)):
        update.message.reply_text(text="Ответ - верный")
        return ConversationHandler.END
    elif user_answer == 'Сдаться':
        return UserStates.QUIT_CHOICE
    else:
        update.message.reply_text(text="Попробуйте снова")
        return UserStates.USERS_ANSWER


def telegram_bot(token):
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    conversation = ConversationHandler(
        entry_points=[CommandHandler(
            'start',
            start
            )
        ],
        states={
            UserStates.NEW_QUESTION_CHOICE: [
                MessageHandler(
                    Filters.text('Новый вопрос'),
                    handle_question,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.text('Сдаться'),
                    cancel
                    )
            ],
            UserStates.USERS_ANSWER: [
                MessageHandler(
                    Filters.text("Сдаться"),
                    cancel
                    ),
                MessageHandler(
                    Filters.text,
                    handle_answer,
                    pass_user_data=True
                    )
            ],
            UserStates.QUIT_CHOICE: [
                MessageHandler(
                    Filters.text("Сдаться"),
                    cancel
                    )
            ]
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
    telegram_bot(tg_bot_token)


if __name__ == '__main__':
    main()
