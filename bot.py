import time
import telebot # библиотека telebot
from config import token # импорт токена

bot = telebot.TeleBot(token)

# для антиспама: id пользователя -> список времени его сообщений
spam_counter = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот для управления чатом.")


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.reply_to_message: # проверка на то, что эта команда была вызвана в ответ на сообщение
        chat_id = message.chat.id # сохранение id чата
        # сохранение id и статуса пользователя, отправившего сообщение
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status
        # проверка пользователя
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "Невозможно забанить администратора.")
        else:
            bot.ban_chat_member(chat_id, user_id) # пользователь с user_id будет забанен в чате с chat_id
            bot.reply_to(message, f"Пользователь @{message.reply_to_message.from_user.username} был забанен.")
    else:
        bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите забанить.")


@bot.message_handler(content_types=['new_chat_members'])
def make_some(message):
    bot.send_message(message.chat.id, 'I accepted a new user!')
    bot.approve_chat_join_request(message.chat.id, message.from_user.id)


@bot.message_handler(content_types=['voice'])
def ban_for_voice(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    status = bot.get_chat_member(chat_id, user_id).status
    # админов не баним
    if status == 'administrator' or status == 'creator':
        return
    bot.ban_chat_member(chat_id, user_id)
    bot.reply_to(message, "Пользователь забанен за голосовое!")


# этот хэндлер ловит все текстовые сообщения, поэтому он ДОЛЖЕН быть последним
@bot.message_handler(func=lambda message: True)
def check_message(message):
    # в личке банить некого
    if message.chat.type == 'private':
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # админов не трогаем
    status = bot.get_chat_member(chat_id, user_id).status
    if status == 'administrator' or status == 'creator':
        return

    # 1. бан за ссылку
    if "https://" in message.text:
        # сохраняем ник и что отправил
        file = open("banned.txt", "a", encoding="utf-8")
        file.write("ник: " + str(message.from_user.username) + "\n")
        file.write("id: " + str(user_id) + "\n")
        file.write("сообщение: " + message.text + "\n")
        file.write("-----\n")
        file.close()

        bot.ban_chat_member(chat_id, user_id)
        bot.reply_to(message, "Пользователь забанен за ссылку!")
        return

    # 2. бан за спам: больше 5 сообщений за 10 секунд
    now = time.time()
    times = spam_counter.get(user_id, [])
    # оставляем только сообщения за последние 10 секунд
    times = [t for t in times if now - t < 10]
    times.append(now)
    spam_counter[user_id] = times

    if len(times) > 5:
        bot.ban_chat_member(chat_id, user_id)
        bot.reply_to(message, "Пользователь забанен за спам!")
        spam_counter[user_id] = []


bot.infinity_polling(none_stop=True)