import telebot
import json
from telebot import types



def openFile(fileName):
    with open(fileName, 'r', encoding='utf-8') as file:
        wordDict = json.load(file)
    return wordDict


def writeFile(fileName, obj):
    with open(fileName, 'w', encoding='utf-8') as file:
        json.dump(obj, file, ensure_ascii=False, indent=4)


Token = openFile('API.json')['Token']

bot = telebot.TeleBot(Token)

ITEM_PER_PAGE = 4
menu_items = [
    {"name": "Грибной суп", "price": 450, "photo": "mushroom_soup.png"},
              {"name": "Салат Цезарь", "price": 550, "photo": "caesar.png"},
              {"name": "Утка с апельсинами", "price": 700, "photo": "duck_orange.png"},
              {"name": "Бефстроганов", "price": 650, "photo": "stroganoff.png"},
              {"name": "Ризотто", "price": 500, "photo": "risotto.png"},
              {"name": "Тирамису", "price": 400, "photo": "tiramisu.png"},
              {"name": "Блины", "price": 300, "photo": "pancakes.png"},
              {"name": "Паста Карбонара", "price": 550, "photo": "carbonara.png"},
              {"name": "Гаспачо", "price": 350, "photo": "gazpacho.png"},
              {"name": "Фалафель", "price": 400, "photo": "falafel.png"}
              ]




def generateStartKeyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Меню')
    button2 = types.KeyboardButton('Корзина')
    button3 = types.KeyboardButton('Заказать')

    keyboard.add(button1, button2)
    keyboard.add(button3)
    return keyboard


def generateMenuKeyboard(page=0):
    keyboard = types.InlineKeyboardMarkup()

    startItem = page * ITEM_PER_PAGE
    endItem = startItem + ITEM_PER_PAGE
    for item in menu_items[startItem:endItem]:
        name = item['name']
        price = item['price']
        button = types.InlineKeyboardButton(f'{name}: {price}', callback_data=f'menu:{name}')
        keyboard.add(button)

    button1 = types.InlineKeyboardButton('<<', callback_data=f'page:-:{page}')
    button2 = types.InlineKeyboardButton('>>', callback_data=f'page:+:{page}')
    if page == 0:
        keyboard.add(button2)
    elif page >= len(menu_items) / ITEM_PER_PAGE - 1:
        keyboard.add(button1)
    else:
        keyboard.add(button1, button2)
    return keyboard


def generateCartkeyboard(userId):
    userId = str(userId)
    keyboard = types.InlineKeyboardMarkup()
    cart = openFile('carts.json').get(userId, {})
    for dish, count in cart.items():
        button1 = types.InlineKeyboardButton('+', callback_data=f'cart:+:{dish}')
        button2 = types.InlineKeyboardButton(f'{dish} x{count}', callback_data='...')
        button3 = types.InlineKeyboardButton('-', callback_data=f'cart:-:{dish}')
        keyboard.add(button2)
        keyboard.add(button1, button3)

    return keyboard


def confirmKeyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button1 = types.KeyboardButton('Да')
    button2 = types.KeyboardButton('Нет')
    keyboard.add(button1, button2)

    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def handleButtonClick(call):
    if 'menu' in call.data:
        dish = call.data.split(':')[1]
        userId = str(call.from_user.id)
        bot.send_message(userId, f'Вы добавили в корзину: {dish}')
        carts = openFile('carts.json')
        cart = carts.get(userId, {})
        cart[dish] = cart.get(dish, 0) + 1
        carts[userId] = cart
        writeFile('carts.json', carts)

    elif 'page' in call.data:
        if '+' in call.data:
            page = int(call.data.split(':')[-1])
            keyboard = generateMenuKeyboard(page + 1)
            bot.edit_message_text('Основное меню:', call.from_user.id, call.message.id, reply_markup=keyboard)
        else:
            page = int(call.data.split(':')[-1])
            keyboard = generateMenuKeyboard(page - 1)
            bot.edit_message_text('Основное меню:', call.from_user.id, call.message.id, reply_markup=keyboard)

    elif 'cart' in call.data:
        userId = str(call.from_user.id)
        keyboard = generateCartkeyboard(userId)
        dish = call.data.split(':')[-1]
        carts = openFile('carts.json')
        cart = carts.get(userId, {})
        if '+' in call.data:
            cart[dish] = cart.get(dish) + 1
        else:
            cart[dish] = cart.get(dish) - 1
            if cart[dish] == 0:
                del cart[dish]

        carts[userId] = cart
        writeFile('carts.json', carts)
        keyboard = generateCartkeyboard(userId)
        bot.edit_message_text('Корзина:', call.from_user.id, call.message.id, reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def sendMessage(message):
    keyboard = generateStartKeyboard()
    bot.send_message(message.from_user.id, 'Привет, это бот для заказа еды.', reply_markup=keyboard)


@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def buttonHandler(message):
    if message.text == 'Меню':
        keyboard = generateMenuKeyboard()
        bot.send_message(message.from_user.id, 'Основное меню:', reply_markup=keyboard)

    elif message.text == 'Корзина':
        keyboard = generateCartkeyboard(message.from_user.id)
        bot.send_message(message.from_user.id, 'Корзина:', reply_markup=keyboard)

    elif message.text == 'Заказать':
        cart = openFile('carts.json').get(str(message.from_user.id), {})
        text = '🛒Ваш заказ: \n'
        for dish, count in cart.items():
            text += f'✨{dish}: {count} \n'

        bot.send_message(str(message.from_user.id), text)
        bot.send_message(str(message.from_user.id), 'Вы подтверждаете заказ?', reply_markup=confirmKeyboard())
        bot.register_next_step_handler_by_chat_id(int(message.from_user.id), confirmOrder)


def confirmOrder(message):
    if message.text == 'Нет':
        keyboard = generateStartKeyboard()
        bot.send_message(message.from_user.id, 'Закакз пока не принят. Вы можете изменить свой заказ.',
                         reply_markup=keyboard)
    elif message.text == 'Да':
        bot.send_message(message.from_user.id, 'Пожалуста, напишите адрес доставки или отправьте геометку Telegram.')
        bot.register_next_step_handler_by_chat_id(int(message.from_user.id), adresHandler)



def adresHandler(message):
    location = 'Напишите текст или геометку Telegram'
    if message.content_type == 'location':
        location = f'{message.location.latitude}, {message.location.longitude}'
    elif message.content_type == 'text':
        location = message.text
    data = openFile('userInfo.json')
    userInfo = data.get(str(message.from_user.id), {})
    userInfo['adres'] = location
    data[str(message.from_user.id)] = userInfo
    writeFile('userInfo.json', data)
    bot.send_message(message.from_user.id, f'Ваш адресс: {userInfo['adres']}', reply_markup=generateStartKeyboard())
    bot.send_message(message.from_user.id, 'Доступна оплата только наличными курьеру.')

@bot.message_handler(commands=['add_info'])
def addInfo(message):
    bot.send_message(message.from_user.id, 'Напишите ваше имя:')
    bot.register_next_step_handler_by_chat_id(int(message.from_user.id), nameHanldler)


def nameHanldler(message):
    data = openFile('userInfo.json')
    name = message.text
    userId = str(message.from_user.id)
    if userId in data:
        data[userId]['name'] = name
    else:
        data[userId] = {'name': name, 'phone': ''}

    writeFile('userInfo.json', data)

    bot.send_message(message.from_user.id, 'Отлично, теперь напишите ваш номер телефона:')
    bot.register_next_step_handler_by_chat_id(int(message.from_user.id), phoneHanldler)


def phoneHanldler(message):
    data = openFile('userInfo.json')
    phone = message.text
    userId = str(message.from_user.id)
    if userId in data:
        data[userId]['phone'] = phone
    else:
        data[userId] = {'name': '', 'phone': phone}

    writeFile('userInfo.json', data)
    bot.send_message(message.from_user.id, 'Готово. Спасибо что поделились с нами информацией')


if __name__ == '__main__':
    bot.polling(non_stop=True)
