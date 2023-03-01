from collections import defaultdict

import openai
import telebot
from dotenv import dotenv_values
from openai.error import TryAgain

config = dotenv_values(".env")

# Устанавливаем API-ключ для OpenAI
openai.api_key = config.get('API_KEY')

# Устанавливаем токен для Telegram бота
bot = telebot.TeleBot(config.get('BOT_TOKEN'))

# Словарь для хранения контекста диалога с каждым пользователем
context_dict = defaultdict(str)

model = "text-davinci-003"

starts = [bot.user.full_name,
          bot.user.username,
          bot.user.first_name,
          "bot", "бот", "тупая машина"]


# Обрабатываем входящие сообщения от пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Проверяем, что сообщение было отправлено нашему боту
    if message.text.startswith('/'):
        return

    if message.chat.type != 'private':
        for i in starts:
            if message.text.lower().startswith(i) or message.text.lower().startswith('@' + i):
                message.text = message.text[len(i):]
                break
        else:
            return
    # bot.send_message(message.chat.id, "Пошел спрашивать у openai")

    # Получаем ID пользователя
    user_id = message.chat.id

    # Получаем текущий контекст диалога с пользователем
    context = context_dict[user_id]

    # Генерируем ответ на основе входящего текста и текущего контекста диалога
    response = generate_response(context + message.text)

    # Сохраняем новый контекст диалога
    context_dict[user_id] = context_dict[user_id] + response['text'] + "\n"

    # Отправляем ответ пользователю, если текст не пустой
    if response['text']:
        bot.reply_to(message, response['text'])


# Генерируем ответ на основе входящего текста и текущего контекста диалога
def generate_response(text):
    model_engine = model
    prompt = f"{text[-500:]}"
    max_tokens = 1024

    # Определяем параметры запроса
    kwargs = {
        "engine": model_engine,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "n": 1,
        "stop": None,
        "temperature": 0.5,
        "timeout": 30
    }
    try:
        response_gen = openai.Completion.create(**kwargs)
    except TryAgain:
        return {'text': "Timeout"}

    return {'text': response_gen.choices[0].text}


# Запускаем бота
bot.polling()
