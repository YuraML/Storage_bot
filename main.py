import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    Filters,
    MessageHandler, Job
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ORDER, ADDRESS, DELIVERY_FROM, USER_ADDRESS, EMAIL, PHONE, CALC, WEIGHT, VOLUME, MONTHS = range(10)

ONE, TWO = range(2)


def start(update, context):
    ''' Приветствие. Всю красотень от Юры вставить сюда  '''

    welcome_message = "Прежде чем начнем, ознакомьтесь со списком разрешенных для хранения вещей, а также ответами на часто задаваемые вопросы."
    permitted_url = "https://docs.google.com/document/d/1l8uWEVuQK_12AQtRFld_XOmEUy6c-2psFkMt9yW6dhE/edit?usp=sharing"
    faq_url = "https://docs.google.com/document/d/1g9wJtZn0RY5mWnnCasIm_T-EQdvyhrP3FBC5BcZxSCk/edit?usp=sharing"

    buttons = [[InlineKeyboardButton("Список разрешенных вещей", url=permitted_url),
                InlineKeyboardButton("FAQ", url=faq_url),
                InlineKeyboardButton("Я ознакомился(-ась)", callback_data="read_everything")]]

    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, reply_markup=reply_markup)
    return ORDER

def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    ''' Рисуем кнопочки меню '''

    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def handle_callback_query(update, context):
    query = update.callback_query
    if query.data == "read_everything":
        context.bot.answer_callback_query(callback_query_id=query.id)
        context.bot.send_message(chat_id=query.message.chat_id, text="Пожалуйста, введите вес вашей посылки (в кг).")
        return WEIGHT


def orderbox(update, context):
    ''' Начинаем оформлять бокс. Список адресов хранения '''

    query = update.callback_query
    if query.data == "read_everything":
        button_list = []
        for addr in adresses:
            button_list.append(InlineKeyboardButton(addr,
                callback_data=addr))

        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        context.bot.send_message(chat_id=update.effective_chat.id,
            text='Пожалуйста, выберите адрес хранения:',
            reply_markup=reply_markup)
        return ADDRESS
    

def delivery_from_method(update, context):
    ''' Сохраняем выбранный адрес хранения и спрашиваем о доставке '''

    query = update.callback_query
    variant = query.data
    query.answer()
    button_list = [
        InlineKeyboardButton('Я сам привезу вещи',
            callback_data=str(ONE)),
        InlineKeyboardButton('Мы вывезем вещи',
            callback_data=str(TWO)),
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    query.edit_message_text(text=f"Вы выбрали адрес хранения: {variant}")

    context.bot.send_message(chat_id=update.effective_chat.id, text="Мы \
        предлагаем бесплатную доставку Ваших вещей из дома на хранение. \
        Хотите воспользоваться?", reply_markup=reply_markup)
    return DELIVERY_FROM


def format_delivery_method(method):
    ''' Представление выбора доставки в удобочитаемый вид '''

    if int(method):
        variant = 'самостоятельную доставку'
    else:
        variant = 'наши услуги по доставке'
    return variant


def pantry_delivery(update, context):
    ''' Сохраняем вид доставки вещей от клиента и спрашиваем адрес '''

    query = update.callback_query
    variant = format_delivery_method(int(query.data))
    query.answer()
    query.edit_message_text(text=f"Вы выбрали: {variant}")
    context.bot.send_message(chat_id=update.effective_chat.id,
            text='Введите адрес, откуда забрать вещи')
    return USER_ADDRESS


def get_user_address(update, context):
    ''' Сохраняем адрес и спрашиваем e-mail '''

    user = update.message.from_user
    user_address = update.message.text
    logger.info('Пользователь %s ввел адрес %s', user.first_name, user_address)
    update.message.reply_text('Введите свой e-mail')
    return EMAIL


def user_delivery(update, context):
    ''' Сохраняем вид доставки и спрашиваем e-mail (для самостоятельных) '''

    query = update.callback_query
    variant = format_delivery_method(query.data)
    query.answer()
    query.edit_message_text(text=f'Вы выбрали: {variant}')

    context.bot.send_message(chat_id=update.effective_chat.id,
        text='Введите свой e-mail')
    return EMAIL


def get_user_email(update, context):
    ''' Сохраняем e-mail и запрашиваем номер телефона '''

    user = update.message.from_user
    user_email = update.message.text
    logger.info('Пользователь %s ввел e-mail %s', user.first_name, user_email)
    update.message.reply_text('Укажите свой номер телефона')
    return PHONE


def get_user_phone(update, context):
    ''' Сохраняем номер телефона и завершаем разговор'''

    user = update.message.from_user
    user_phone = update.message.text
    logger.info('Пользователь %s ввел телефон %s', user.first_name, user_phone)
    update.message.reply_text('Давайте рассчитаем примерную стоимость хранения')
    context.bot.send_message(chat_id=update.effective_chat.id,
        text='Пожалуйста, введите вес Ваших вещей (в кг.)')
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


def ask_again(update, context):
    ''' Повторный запрос данных '''
    
    context.bot.send_message(chat_id=update.effective_chat.id,
        text='Вы ввели не корректные данные. Попробуйте еще раз ввести e-mail')
    print(context.matches)
    return EMAIL


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


adresses = ['Адрес 1', 'Адрес 2', 'Адрес 3']
SELECTED_ADDRESS = list(range(len(adresses)))


def main():
    TOKEN = '6265890695:AAEFXFkuGxpElm_qaodxgRGSGg_UYud2vkg'

    updater = Updater(token=TOKEN)

    app = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states = {
            ORDER: [CallbackQueryHandler(orderbox)],
            ADDRESS: [CallbackQueryHandler(delivery_from_method)],
            DELIVERY_FROM: [CallbackQueryHandler(pantry_delivery, pattern='^' + str(TWO) + '$'),
                            CallbackQueryHandler(user_delivery, pattern='^' + str(ONE) + '$')],
            USER_ADDRESS: [MessageHandler(None, get_user_address)],
            EMAIL: [MessageHandler(Filters.regex('@'+'.'), get_user_email)],
            PHONE: [MessageHandler(Filters.regex('[0-9]'), get_user_phone)],
            CALC: [CallbackQueryHandler(handle_callback_query)],
            WEIGHT: [MessageHandler(Filters.text & ~Filters.command, handle_weight)],
            VOLUME: [MessageHandler(Filters.text & ~Filters.command, handle_volume)],
            MONTHS: [MessageHandler(Filters.text & ~Filters.command, handle_months)],
        },
        fallbacks = [MessageHandler(Filters.regex('@|.'), ask_again),
                    MessageHandler(Filters.command, handle_invalid_input)]
    )
    app.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()