import logging
import os
import random

import telegram

from dotenv import load_dotenv
from telegram import ForceReply
from telegram import Update
from telegram.ext import Filters
from telegram.ext import CommandHandler
from telegram.ext import CallbackContext
from telegram.ext import MessageHandler
from telegram.ext import Updater

from parse_file import create_parsed_description


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger('Logger')


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Посмотреть счёт']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard,
                                                one_time_keyboard=True
                                                )
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup,
    )


def handle_question(update: Update, context: CallbackContext) -> None:
    quiz_dict, title = create_parsed_description()
    question, answer = random.choice(quiz_dict[title]).values()
    print(question)
    if update.message.text == "Новый вопрос":
        update.message.reply_text(text=question)


def telegram_bot(token):
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command,
        handle_question
        ))
    updater.start_polling()
    updater.idle()


def main():
    load_dotenv()
    tg_bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    telegram_bot(tg_bot_token)


if __name__ == '__main__':
    main()
