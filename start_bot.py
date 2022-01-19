import telebot
from telebot import types
import re
import bs4
import requests
import config
import data_base_user

bot = telebot.TeleBot(config.token)

keyboard = types.InlineKeyboardMarkup(row_width=1)
key_yes = types.InlineKeyboardButton(text='Покажи квартиры', callback_data='yes')
keyboard.add(key_yes)
key_price = types.InlineKeyboardButton(text='Узнать цену аренды', callback_data='price')
keyboard.add(key_price)
button_price = types.InlineKeyboardButton(text='Меняем цену аренды', callback_data='change')
keyboard.add(button_price)
reset = types.InlineKeyboardButton(text='Сброс', callback_data='reset')
site_vk = types.InlineKeyboardButton(text='Перейти в группу ВК', url="https://vk.com/kvartira_irkutsk")
keyboard.row(reset, site_vk)


# По команде /start начало диалога
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.from_user.id, "Привет! Что будем делать?", reply_markup=keyboard)


# По команде /reset будем возвращаться к началу диалога
def cmd_reset(message):
    bot.send_message(message.chat.id, "Все настройки сброшены!")
    bot.send_message(message.chat.id, "Что делаем?", reply_markup=keyboard)
    data_base_user.set_user_price(message.chat.id, 16000)

# При получении любого сообщения от пользователя
@bot.message_handler(content_types=['text'])
def random_user_message(message):
    bot.send_message(message.chat.id, "Я тебя не понимаю!")
    bot.send_message(message.from_user.id, "Что будем делать?", reply_markup=keyboard)


def change_price(message):
    if message.text.isdigit():
        bot.send_message(message.chat.id, "Теперь цена: " + message.text)
        data_base_user.set_user_price(message.chat.id, message.text)
        bot.send_message(message.from_user.id, "Что делаем?", reply_markup=keyboard)
    else:
        if message.text == "/reset":
            cmd_reset(message)
            return
        else:
            msg_bot = bot.send_message(message.chat.id, "Ошибка! Введите число!")
            bot.register_next_step_handler(msg_bot, change_price)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    price = data_base_user.get_current_price(call.message.chat.id)
    if call.data == "yes":
        Search(price)
        if flag_search == 1:
            bot.send_message(call.message.chat.id, "Вот список квартир до " + price)
            for k in houses:
                bot.send_message(call.message.chat.id, k)
        else:
            bot.send_message(call.message.chat.id,
                             "Пока что квартир с ценой" + " " + str(price) + " " + "нет :(" + "\n" + "Попробуй попозже")
        bot.send_message(call.message.chat.id, "Что делаем?", reply_markup=keyboard)
    elif call.data == "price":
        bot.send_message(call.message.chat.id, 'Сейчас цена: ' + str(price))
        bot.send_message(call.message.chat.id, "Что делаем?", reply_markup=keyboard)
    elif call.data == "change":
        msg_bot = bot.send_message(call.message.chat.id, 'Введи желаемую цену аренды')
        bot.register_next_step_handler(msg_bot, change_price)
    elif call.data == "reset":
        cmd_reset(call.message)


if __name__ == "__main__":
    print("Вроде все работает!")
    flag_search = 0
    houses = []

    def Search(price_user):
        houses.clear()
        global flag_search
        flag_search = 0
        res = requests.get("https://vk.com/kvartira_irkutsk")
        soup = bs4.BeautifulSoup(res.text, 'html5lib')
        if price_user is None:
            price_user = 16000
        for j in soup.select('.wall_item'):
            info = j.find_all("div", {"class": "pi_text"})[0].text
            district = re.search(r'.* (Танк|Октябрьский|Правобережный|Ленинский)', info)
            price = re.match(r'\d+', info)
            if price is not None:
                price = int(info[0:5])
                if price <= int(price_user) and district:
                    site = info + "\n" + "Ссылка:" + "https://vk.com/kvartira_irkutsk?w=wall" + j.div.a["data-post-id"]
                    houses.append(site)
                    flag_search = 1
        if flag_search == 0:
            houses.append("Ничего не найдено :(")
        return houses, flag_search

bot.polling(none_stop=True, interval=0)
