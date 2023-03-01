import telebot
import openai
from dotenv import dotenv_values

from collections import defaultdict

config = dotenv_values(".env")

# Устанавливаем API-ключ для OpenAI
openai.api_key = config.get('API_KEY')

# Устанавливаем токен для Telegram бота
bot = telebot.TeleBot(config.get('BOT_TOKEN'))

# Словарь для хранения контекста диалога с каждым пользователем
context_dict = defaultdict(str)

model = "text-davinci-003"

# Обрабатываем входящие сообщения от пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Проверяем, что сообщение было отправлено нашему боту
    if message.text.startswith('/'):
        return

    # Получаем ID пользователя
    user_id = message.chat.id

    # Получаем текущий контекст диалога с пользователем
    context = context_dict[user_id]

    # Генерируем ответ на основе входящего текста и текущего контекста диалога
    response = generate_response(context+message.text)

    # Сохраняем новый контекст диалога
    context_dict[user_id] = context_dict[user_id] + response['text'] + "\n"

    # Отправляем ответ пользователю, если текст не пустой
    if response['text']:
        bot.reply_to(message, response['text'])


# Генерируем ответ на основе входящего текста и текущего контекста диалога
def generate_response(text):
    model_engine = model
    prompt = f"{text}"
    max_tokens = 1024

    # Определяем параметры запроса
    kwargs = {
        "engine": model_engine,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "n": 1,
        "stop": None,
        "temperature": 0.5,
    }
    response_gen = openai.Completion.create(**kwargs)
    return {'text': response_gen.choices[0].text}


# Запускаем бота
bot.polling()
