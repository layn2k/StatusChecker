from config import OLLAMA_URL, TELEGRAM_TOKEN, MODEL
import telebot
import ollama
from datetime import datetime, date
import time
from prompts import EXTRACT_TITLE, SUMMARIZATION, STATUS

bot = telebot.TeleBot(TELEGRAM_TOKEN)
daily_history = []

daily_data = {
    'status': {},
    'report': {}
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот для сводок проектов. Используйте:\n#статус <Название проекта>: <что требуется сделать>\n#отчет <Название проекта>: <что сделано>")

@bot.message_handler(commands=['status_info'])
def short_status(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Собираю короткую сводку по статусам')
    for status in daily_data['status']:
        bot.reply_to(message, ollama.generate(model=MODEL, system=STATUS, think = False, prompt=status + daily_data['status'][status]).response)

@bot.message_handler(commands=['summary'])
def summary(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Начинаю подведение итогов')
    for status in daily_data['status']:
        bot.reply_to(message, ollama.generate(model=MODEL, system = SUMMARIZATION, think = False, prompt=status + "\n" + daily_data['status'][status] + "\n" + "\n\n".join(daily_data['report'][status])).response)

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text
    if '#статус' in text.lower():
        process_status(text, message)
    elif '#отчет' in text.lower():
        process_report(text, message)

def process_status(text, message):
    project_name = extract_project_name(text)
    if project_name not in daily_data['status']:
        daily_data['status'][project_name] = str()
    daily_data['status'][project_name]= text

def process_report(text, message):
    project_name = extract_project_name(text)
    if not project_name:
        bot.reply_to(message, "Укажите название проекта после #отчет")
        return
    elif project_name not in daily_data['status']:
        bot.reply_to(message, f"Сначала создайте статус для проекта '{project_name}'")
        return
    else:
        daily_data['report'][project_name] = []
        daily_data['report'][project_name].append(text)

def extract_project_name(text):
    return ollama.generate(model = MODEL, system = EXTRACT_TITLE, prompt=text, think=False, options={'temperature': 0.0, 'num_predict': 30}).response

bot.infinity_polling()
