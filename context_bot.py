import logging
import queue
import threading
import uuid
from collections import defaultdict, deque

import openai
import telebot
from dotenv import dotenv_values
from openai.error import OpenAIError

from db_manager import add_message, get_or_create_user, update_balance, get_balance, set_admin, check_admin, \
    get_userlist

logging.basicConfig(level=logging.INFO)

config = dotenv_values(".env")

# Устанавливаем API-ключ для OpenAI
openai.api_key = config.get('API_KEY')

# Устанавливаем токен для Telegram бота
bot = telebot.TeleBot(config.get('BOT_TOKEN'))

# Словарь для хранения контекста диалога с каждым пользователем
context_dict = defaultdict(lambda: deque(maxlen=10))

model = "gpt-3.5-turbo"

starts = [bot.user.full_name,
          bot.user.username,
          bot.user.first_name,
          "bot", "бот", "тупая машина", "MBA Intern", "Intern", "сударь"]


# Обрабатываем входящие сообщения от пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Проверяем, что сообщение было отправлено нашему боту
    if message.text.startswith('/'):
        process_commands(message)
        return
    # Получаем ID пользователя
    chat_id = message.chat.id
    username = message.chat.username

    user = get_or_create_user(chat_id, username)
    if user.balance <= 0:
        bot.reply_to(message, "У вас не осталось доступных сообщений.")
        return

    # Получаем текущий контекст диалога с пользователем
    context = context_dict[chat_id]
    context.append({'role': 'user', 'content': message.text})

    bot.send_chat_action(message.chat.id, 'typing')
    # Генерируем ответ на основе входящего текста и текущего контекста диалога
    # response = generate_response(list(context))

    # Запускаем функцию generate_response в отдельном потоке
    response_queue = queue.Queue()
    generate_thread = threading.Thread(target=generate_response, args=(list(context), response_queue))
    generate_thread.start()

    generate_thread.join(timeout=20)

    if generate_thread.is_alive():
        # Если поток все еще работает, то запускаем отправку сообщения в отдельном потоке
        bot.send_message(message.chat.id, "Нужно еще немного времени...")
        bot.send_chat_action(message.chat.id, 'typing')

    response = response_queue.get()

    # Отправляем ответ пользователю, если текст не пустой
    if response:
        context.append(response)
        bot.reply_to(message, response['content'])
        add_message(chat_id, username, message.text, role='user')  # Запись сообщения пользователя
        add_message(chat_id, username, response['content'], role='assistant')  # Запись ответа бота
        update_balance(username, -1)  # Списание одного сообщения
    else:
        bot.send_message("Api error", chat_id=chat_id)


# Генерируем ответ на основе входящего текста и текущего контекста диалога
def generate_response(context, queue):
    salt = f"[{uuid.uuid4().hex}]"
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=context
        )
        resp = response['choices'][0]['message']
    except OpenAIError as e:
        logging.error(salt + f'OpenAI Error: {e}')
        return {'text': "OpenAI Error"}
    except TimeoutError:
        logging.info(salt + f'Got timeout')
        return {'text': "Timeout"}
    if not (len(resp)):
        resp = "Empty openai answer"
    queue.put(resp)
    return resp


def process_commands(message):
    # if message.text.startswith('/top_up'):
    #     top_up_command(message)
    if message.text.startswith('/balance'):
        balance_command(message)
    elif message.text.startswith('/add_messages'):
        add_messages_command(message)
    elif message.text.startswith('/set_admin'):
        set_admin_command(message)
    elif message.text == '/start':
        send_start_message(message)
    elif message.text == '/user_list':
        user_list_command(message)


def set_admin_command(message):
    chat_id = message.chat.id
    if check_admin(chat_id):
        username = message.text.split('/set_admin').pop()
        if username:
            set_admin(username)
            bot.reply_to(message, f"Пользователь {username} назначен администратором.")
        else:
            bot.reply_to(message, "Укажите имя пользователя.")
    else:
        bot.reply_to(message, "У вас нет прав администратора.")


def balance_command(message):
    username = message.chat.username
    balance = get_balance(username)
    bot.reply_to(message, f"Текущий баланс: {balance} сообщений.")


def send_start_message(message):
    bot.send_message(message.chat.id, f"""
    /balance - проверить остаток сообщения""")


def add_messages_command(message):
    chat_id = message.chat.id
    if check_admin(chat_id):
        args = message.text.split(' ')
        if len(args) == 3:
            username = str(args[1])
            amount = int(args[2])
            update_balance(username, amount)
            bot.reply_to(message,
                         f"Пользователю {username} добавлено {amount} сообщений. Текущий баланс: {get_balance(username)} сообщений.")
        else:
            bot.reply_to(message, "Используйте команду в формате: /add_messages user_id amount")
    else:
        bot.reply_to(message, "У вас нет прав администратора.")



def user_list_command(message):
    chat_id = message.chat.id
    if check_admin(chat_id):
        users = get_userlist()
        resp = ''
        for u in users:
            resp += f'{u.chat_id}. @{u.username} - {u.balance} сообщений, {u.is_admin}\n'
        bot.reply_to(message, resp)


    else:
        bot.reply_to(message, "У вас нет прав администратора.")


bot.polling()
