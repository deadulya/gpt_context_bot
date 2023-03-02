import logging
import uuid
from collections import defaultdict, deque

import openai
import telebot
from dotenv import dotenv_values
from openai.error import OpenAIError

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
          "bot", "бот", "тупая машина", "MBA Intern", "Intern"]


# Обрабатываем входящие сообщения от пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Проверяем, что сообщение было отправлено нашему боту
    if message.text.startswith('/'):
        return

    if message.chat.type != 'private':
        for i in starts:
            if message.text.lower().startswith(i) or message.text.lower().startswith('@' + i.lower()):
                message.text = message.text[len(i):]
                break
        else:
            return

    # Получаем ID пользователя
    chat_id = message.chat.id

    # Получаем текущий контекст диалога с пользователем
    context = context_dict[chat_id]
    context.append({'role': 'user', 'content': message.text})

    # Генерируем ответ на основе входящего текста и текущего контекста диалога
    response = generate_response(list(context))

    # Отправляем ответ пользователю, если текст не пустой
    if response:
        context.append(response)
        bot.reply_to(message, response['content'])
    else:
        bot.send_message("Api error", chat_id=chat_id)


# Генерируем ответ на основе входящего текста и текущего контекста диалога
def generate_response(context):
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
    return resp


bot.polling()
