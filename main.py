import logging
import os
import re

from dotenv import load_dotenv


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    Filters,
    MessageHandler
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ADDRESS, DELIVERY_FROM, USER_ADDRESS, EMAIL, PHONE, CALC, WEIGHT, DELIVERY_TO, \
    VOLUME, MONTHS, CHOICE, HANDL_CHOICE, DETAIL, FETCH, ADDRESS_TO, \
    PERSONAL = range(16)

ONE, TWO = range(2)


def start(update, context):
    ''' Приветствие. Всю красотень от Юры вставить сюда  '''

    welcome_message = "Прежде чем начнем, ознакомьтесь со списком разрешенных для хранения вещей, а также ответами на часто задаваемые вопросы."
    permitted_url = "https://docs.google.com/document/d/1l8uWEVuQK_12AQtRFld_XOmEUy6c-2psFkMt9yW6dhE/edit?usp=sharing"
    faq_url = "https://docs.google.com/document/d/1g9wJtZn0RY5mWnnCasIm_T-EQdvyhrP3FBC5BcZxSCk/edit?usp=sharing"

    buttons = [[InlineKeyboardButton("Список разрешенных вещей", callback_data="permitted_items"),
                InlineKeyboardButton("FAQ", callback_data="FAQ"),
                InlineKeyboardButton("Я ознакомился(-ась)", callback_data="read_everything")]]

    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, reply_markup=reply_markup)
    return CHOICE


def get_user_choice(update, context):
    ''' Выбор действия пользователем '''

    query = update.callback_query
    if query.data == "read_everything":
        button_list = [
            InlineKeyboardButton('Оформить заказ', callback_data='orderbox'),
            InlineKeyboardButton('Список действующих боксов', callback_data='user_boxes'),
            InlineKeyboardButton('Выход', callback_data='exit'),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        query.edit_message_text(text='Выберите действие', reply_markup=reply_markup)
        return HANDL_CHOICE
    elif query.data == 'permitted_items':
        text = '''
Что принимается на хранение:

 Мебель
 Бытовая техника
 Одежда и обувь
 Инструменты
 Посуда
 Книги
 Шины
 Велосипеды
 Мотоциклы и скутеры
 Спортивный инвентарь

Что не принимается на хранение:

 Алкоголь
 Продукты
 Деньги и драгоценности
 Изделия из натурального меха
 Живые цветы и растения
 Домашние питомцы
 Оружие и боеприпасы
 Взрывоопасные вещества и токсины
 Лаки и краски в негерметичной таре
 Любой мусор и отходы
 
'''
        buttons = [InlineKeyboardButton("FAQ", callback_data="FAQ"),
                   InlineKeyboardButton("Я ознакомился(-ась)", callback_data="read_everything")]

        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)

    elif query.data == 'FAQ':
        text = '''
Как происходит оплата?

 Вы можете оплатить хранение на нашем складе картой любого банка, привязав её во время сдачи вещей. Первый платеж будет списан, как только вещи попадут на склад. Это может занять до 24 часов после встречи с муверами. Вы сразу получите уведомление в личном кабинете и по смс. Списания по тарифу происходят один раз в месяц, того же числа, что и первое списание.

Насколько заранее нужно заказывать сдачу вещей? А возврат?

 Обычно мы можем приехать на следующий день после оформления заявки, но рекомендуем делать заказ за два-три дня.

Как происходит сдача вещей?

 После оформления заказа мы свяжемся с вами, чтобы уточнить все детали. Утром в день сдачи позвоним, чтобы сказать точное время приезда муверов. Муверы приедут к вам в назначенный день и время, упакуют вещи, погрузят в автомобиль и повезут на склад.


Как рассчитывается стоимость хранения вещей?

 Оставьте ваши контактные данные. Мы вам перезвоним, чтобы рассчитать стоимость хранения вещей. Для этого потребуется описание или фото предметов, которые вы хотите сдать. Тариф рассчитывается по кубическим метрам. Габариты вещей сложной формы, таких как диван, кресло или стул, мы измеряем по объему описанного вокруг них прямоугольника. Итоговую цену мы фиксируем в момент сдачи. Муверы сообщат вам тариф, и вы сможете подтвердить его или изменить количество вещей. Услуги упаковки и транспортировки вещей уже включены в стоимость тарифа, ведь мы — ответственная компания, которая предлагает решение под ключ. Мы оказываем услуги временного и длительного хранения на срок от 1 месяца — вы можете продлевать аренду индивидуального места на складе каждый месяц.
'''
        buttons = [InlineKeyboardButton("Список разрешенных вещей", callback_data="permitted_items"),
                   InlineKeyboardButton("Я ознакомился(-ась)", callback_data="read_everything")]

        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)



def personal_data_consent(update, context):
    query = update.callback_query
    user = query.from_user
    logger.info(f'Пользователь %s на соглашение о перс.данных ответил %s',
                user.first_name, query.data)
    if query.data == 'no':
        query.edit_message_text(text='Приятно было с Вами пообщаться. До свидания.')
        return ConversationHandler.END
    elif query.data == 'yes':
        button_list = []
        for addr in adresses:
            button_list.append(InlineKeyboardButton(addr,
                                                    callback_data=addr))
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        query.edit_message_text(text='Пожалуйста, выберите адрес хранения:',
                                reply_markup=reply_markup)
        return ADDRESS


def handle_choice(update, context):
    ''' Начинаем оформлять заказ либо смотреть список активных заказов '''

    query = update.callback_query
    user = query.from_user
    if query.data == 'orderbox':
        query = update.callback_query
        text = '''Прежде чем наччнем, ознакомьтесь с условиями по обработке персональных данных. 
        Настоящим подтверждаю, что я ознакомлен и согласен с условиями Политики в отношении обработки персональных данных. Настоящим я даю разрешение ООО "Кладовка" (далее "Кладовка") в целях информирования об услугах, заключения и исполнения договора предоставления услуг обрабатывать - собирать, записывать, хранить, уточнять, извлекать, использовать, удалять, уничтожать - мои персональные данные: номер телефона, адрес электронной почты и почтовый адрес. Также я разрешаю "Кладовке" в целях информирования осуществлять обработку вышеперечисленных персональных данных и направлять на указанный мною адрес электронной почты и/или на номер мобильного телефона, а также с помощью системы мгновенного обмена сообщениями через Интернет информацию об услугах "Кладовки" и ее партнеров. Согласие может быть отозвано мною в любой момент путем направления письменного уведомления по адресу "Кладовки".'''
        button_list = [
            InlineKeyboardButton('Согласен', callback_data='yes'),
            InlineKeyboardButton('Не согласен', callback_data='no'),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        query.edit_message_text(text=text, reply_markup=reply_markup)
        return PERSONAL
    elif query.data == 'user_boxes':
        button_list = []
        boxes = ['Box 1', 'Box 2', 'Box 3']
        for box in boxes:
            button_list.append(InlineKeyboardButton(box,
                                                    callback_data=box))
        button_list.append(InlineKeyboardButton('Назад', callback_data='back'))
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
        query.edit_message_text(text='Ваши активные заказы',
                                reply_markup=reply_markup)
        return DETAIL
    elif query.data == 'exit':
        query.edit_message_text(text='Приятно было пообщаться с Вами')
        return ConversationHandler.END


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


def show_detail(update, context):
    '''
    Здесь надо будет нарисовать в сообщении что-то типа:
    Апельсины в бочках,
    адрес такой-то, оплачено хранение до такого-то
    '''
    query = update.callback_query
    user = query.from_user
    if query.data == 'back':
        button_list = [
            InlineKeyboardButton('Оформить заказ', callback_data='orderbox'),
            InlineKeyboardButton('Список действующих боксов', callback_data='user_boxes'),
            InlineKeyboardButton('Выход', callback_data='exit'),
        ]
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        query.edit_message_text(text='Выберите действие', reply_markup=reply_markup)
        return HANDL_CHOICE
    lable = 'Апельсины в бочках'
    addr = 'Адрес на Кудыкиной горе'
    end_date = '31.12.2024'
    button_list = [
        InlineKeyboardButton('Хочу забрать вещи', callback_data='fetch'),
        InlineKeyboardButton('Назад', callback_data='cancel')
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    query.edit_message_text(
        text=f'{lable}\nАдрес склада: {addr}\nХранение до: {end_date}'
    )
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Храним дальше?', reply_markup=reply_markup)
    return FETCH


def fetch(update, _):
    query = update.callback_query
    if query.data == 'cancel':
        button_list = []
        boxes = ['Box 1', 'Box 2', 'Box 3']
        for box in boxes:
            button_list.append(InlineKeyboardButton(box,
                                                    callback_data=box))
        button_list.append(InlineKeyboardButton('Назад', callback_data='back'))
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
        query.edit_message_text(text='Ваши активные заказы',
                                reply_markup=reply_markup)
        return DETAIL
    button_list = [
        InlineKeyboardButton('Нет, я заберу свои вещи', callback_data='self'),
        InlineKeyboardButton('Привезите мне вещи', callback_data='delivery_to'),
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    query.edit_message_text(text='Можем предложить Вам доставку вещей', reply_markup=reply_markup)
    return DELIVERY_TO


def delivery_to_address(update, _):
    query = update.callback_query
    if query.data == 'self':
        query.edit_message_text(text='Можете забрать вещи с 8-00 до 22-00. Было приятно работать с Вами.')
        return ConversationHandler.END
    elif query.data == 'delivery_to':
        query.edit_message_text(text='Укажите, пожалуйста, адрес, куда необходимо доставить вещи')
        return ADDRESS_TO


def get_address_to(update, context):
    ''' Сохраняем адрес доставки вещей '''

    address_to = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Мы свяжемся с Вами для уточнения времени доставки. Благодарим за использование наших услуг.')
    return ConversationHandler.END


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


def get_user_address(update, _):
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
    if re.search(r'@', user_email) and re.search(r'.', user_email):
        logger.info('Пользователь %s ввел e-mail %s', user.first_name, user_email)
        update.message.reply_text('Укажите свой номер телефона')
        return PHONE
    update.message.reply_text('Вы ввели некорректные данные. Попробуйте еще раз')
    return EMAIL


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

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Заказ создан. Мы свяжемся с Вами для уточнения деталей. Благодарим за Ваш выбор!")
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
                             text='Вы ввели не корректные данные. Попробуйте еще раз')
    print(context.matches)
    return PHONE


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
    load_dotenv()
    TOKEN = os.environ['TOKEN']

    updater = Updater(token=TOKEN)

    app = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PERSONAL: [CallbackQueryHandler(personal_data_consent)],
            CHOICE: [CallbackQueryHandler(get_user_choice)],
            HANDL_CHOICE: [CallbackQueryHandler(handle_choice)],
            DETAIL: [CallbackQueryHandler(show_detail)],
            ADDRESS: [CallbackQueryHandler(delivery_from_method)],
            DELIVERY_FROM: [CallbackQueryHandler(pantry_delivery, pattern='^' + str(TWO) + '$'),
                            CallbackQueryHandler(user_delivery, pattern='^' + str(ONE) + '$')],
            USER_ADDRESS: [MessageHandler(None, get_user_address)],
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_user_email)],
            PHONE: [MessageHandler(Filters.regex('[0-9]'), get_user_phone)],
            CALC: [CallbackQueryHandler(handle_callback_query)],
            WEIGHT: [MessageHandler(Filters.text & ~Filters.command, handle_weight)],
            VOLUME: [MessageHandler(Filters.text & ~Filters.command, handle_volume)],
            MONTHS: [MessageHandler(Filters.text & ~Filters.command, handle_months)],
            FETCH: [CallbackQueryHandler(fetch)],
            DELIVERY_TO: [CallbackQueryHandler(delivery_to_address)],
            ADDRESS_TO: [MessageHandler(Filters.text & ~Filters.command, get_address_to)],
        },
        fallbacks=[MessageHandler(Filters.regex('@|.'), ask_again),
                   MessageHandler(Filters.command, handle_invalid_input)]
    )
    app.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()