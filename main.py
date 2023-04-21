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

ADDRESS, DELIVERY_FROM, USER_ADDRESS, EMAIL, PHONE = range(5)

ONE, TWO = range(2)


def start(update, context):
    ''' Приветствие. Всю красотень от Юры вставить сюда  '''

    user = update.message.from_user
    logger.info('Пользователь %s начал разговор.', user.first_name)
    context.bot.send_message(chat_id=update.effective_chat.id, 
        text="Мы расширяем Ваше пространство хранения вещей")


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


def orderbox(update, _):
    ''' Начинаем оформлять бокс. Список адресов хранения '''

    user = update.message.from_user
    logger.info('Пользователь %s решил оформить бокс', user.first_name)
    button_list = []
    for addr in adresses:
        button_list.append(InlineKeyboardButton(addr,
            callback_data=addr))

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    update.message.reply_text('Пожалуйста, выберите адрес хранения:',
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


def get_user_phone(update, _):
    ''' Сохраняем номер телефона и завершаем разговор'''

    user = update.message.from_user
    user_phone = update.message.text
    logger.info('Пользователь %s ввел телефон %s', user.first_name, user_phone)
    update.message.reply_text('Благодарим за Ваш заказ')
    return ConversationHandler.END


def ask_again(update, context):
    ''' Повторный запрос данных '''
    
    context.bot.send_message(chat_id=update.effective_chat.id,
        text='Вы ввели не корректные данные. Попробуйте еще раз ввести e-mail')
    print(context.matches)
    return EMAIL


adresses = ['Адрес 1', 'Адрес 2', 'Адрес 3']
SELECTED_ADDRESS = list(range(len(adresses)))


if __name__ == '__main__':
    TOKEN = '6265890695:AAEFXFkuGxpElm_qaodxgRGSGg_UYud2vkg'

    updater = Updater(token=TOKEN)

    app = updater.dispatcher

    app.add_handler(CommandHandler('start', start))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('orderbox', orderbox)],
        states = {
            ADDRESS: [CallbackQueryHandler(delivery_from_method)],
            DELIVERY_FROM: [CallbackQueryHandler(pantry_delivery, pattern='^' + str(TWO) + '$'),
                            CallbackQueryHandler(user_delivery, pattern='^' + str(ONE) + '$')],
            USER_ADDRESS: [MessageHandler(None, get_user_address)],
            EMAIL: [MessageHandler(Filters.regex('@'+'.'), get_user_email)],
            PHONE: [MessageHandler(Filters.regex('[0-9]'), get_user_phone)]
        },
        fallbacks = [MessageHandler(Filters.regex('@|.'), ask_again)]
    )
    app.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()