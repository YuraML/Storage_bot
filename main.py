import os
import telegram

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

WEIGHT, VOLUME, MONTHS = range(3)


def calculate_the_order_cost(order_weight, order_volume, months):
    order_cost = 0
    initial_price = 1500

    if 0 < order_weight < 10:
        order_cost += initial_price
    elif 10 <= order_weight < 25:
        order_cost += initial_price * 1.2
    elif 25 <= order_weight < 40:
        order_cost += initial_price * 1.4
    elif 40 <= order_weight < 70:
        order_cost += initial_price * 1.6
    elif 70 <= order_weight < 100:
        order_cost += initial_price * 1.8
    elif order_weight >= 100:
        order_cost += initial_price * 2

    if 0 < order_volume < 3:
        order_cost *= 2
    elif 3 <= order_volume < 7:
        order_cost *= 2.2
    elif 7 <= order_volume < 10:
        order_cost *= 2.4
    elif 10 <= order_volume < 13:
        order_cost *= 2.6
    elif 13 <= order_volume < 17:
        order_cost *= 2.8
    elif 17 <= order_volume:
        order_cost *= 3

    return order_cost * months


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
        context.bot.send_message(chat_id=query.message.chat_id, text="Пожалуйста, введите вес вашей посылки (в кг).")
        return WEIGHT


def handle_weight(update, context):
    weight = update.message.text.strip()
    if weight.isnumeric() and 0 < int(weight):
        context.user_data['weight'] = int(weight)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Пожалуйста, укажите объем вашей посылки (в м2).")
        return VOLUME
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Недопустимый вес. Пожалуйста, введите положительное число, большее 0.")
        return WEIGHT


def handle_volume(update, context):
    volume = update.message.text.strip()
    if volume.isnumeric() and 0 < int(volume):
        context.user_data['volume'] = int(volume)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Пожалуйста, укажите сколько месяцев вы хотите хранить посылку.")
        return MONTHS
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Недопустимый объем. Пожалуйста, введите положительное число, большее 0.")
        return VOLUME


def handle_months(update, context):
    months = update.message.text.strip()
    if months.isnumeric() and 0 < int(months) <= 24:
        context.user_data['months'] = int(months)

        order_weight = context.user_data['weight']
        order_volume = context.user_data['volume']
        order_cost = calculate_the_order_cost(order_weight, order_volume, int(months))

        order_cost = round(order_cost)
        if order_cost is not None:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Стоимость хранения вашей посылки составляет: {order_cost} рублей.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Извините, не удалось рассчитать стоимость хранения. Пожалуйста, проверьте правильность введенных данных.")

        context.bot.send_message(chat_id=update.effective_chat.id, text="Спасибо! Заказ создан.")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Введите количество месяцев (до 24).")
        return MONTHS


def handle_invalid_input(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Неверный ввод. Пожалуйста, попробуйте снова.")
    return WEIGHT


def main():
    load_dotenv()
    bot = telegram.Bot(token=os.environ['TOKEN'])
    updater = Updater(bot=bot, use_context=True)

    conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback_query)],
        states={
            WEIGHT: [MessageHandler(Filters.text & ~Filters.command, handle_weight)],
            VOLUME: [MessageHandler(Filters.text & ~Filters.command, handle_volume)],
            MONTHS: [MessageHandler(Filters.text & ~Filters.command, handle_months)]

        },
        fallbacks=[MessageHandler(Filters.command, handle_invalid_input)]
    )

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start_bot)
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(conversation_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
