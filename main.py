import os
import telegram

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler


def start_bot(update, context):
    welcome_message = "Прежде чем начнем, ознакомьтесь со списком разрешенных для хранения вещей, а также ответами на часто задаваемые вопросы."
    permitted_url = "https://docs.google.com/document/d/1l8uWEVuQK_12AQtRFld_XOmEUy6c-2psFkMt9yW6dhE/edit?usp=sharing"
    faq_url = "https://docs.google.com/document/d/1g9wJtZn0RY5mWnnCasIm_T-EQdvyhrP3FBC5BcZxSCk/edit?usp=sharing"

    buttons = [[InlineKeyboardButton("Список разрешенных вещей", url=permitted_url),
                InlineKeyboardButton("FAQ", url=faq_url),
                InlineKeyboardButton("Я ознакомился(-ась)", callback_data="read_everything")]]

    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, reply_markup=reply_markup)


def handle_callback_query(update, context):
    query = update.callback_query
    if query.data == "read_everything":
        context.bot.answer_callback_query(callback_query_id=query.id)
        context.bot.send_message(chat_id=query.message.chat_id, text="Отлично! Укажите ваш адрес.")


def main():
    load_dotenv()
    bot = telegram.Bot(token=os.environ['TOKEN'])
    updater = Updater(bot=bot, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start_bot)
    dispatcher.add_handler(start_handler)

    callback_query_handler = CallbackQueryHandler(handle_callback_query)
    dispatcher.add_handler(callback_query_handler)
    updater.start_polling()


if __name__ == '__main__':
    main()
