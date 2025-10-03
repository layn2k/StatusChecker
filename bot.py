from config import OLLAMA_URL, TELEGRAM_TOKEN, MODEL, DB, CHAT_ID
import telebot
import ollama
from prompts import EXTRACT_TITLE, SUMMARIZATION, STATUS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime, date

bot = telebot.TeleBot(TELEGRAM_TOKEN)
daily_history = []
client = MongoClient(DB)
db = client["bot"]
collection = db["status_report"]

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот для сводок проектов. Используйте:\n#статус <Название проекта>: <что требуется сделать>\n#отчет <Название проекта>: <что сделано>")

@bot.message_handler(commands=['status_info'])
def short_status(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Собираю короткую сводку по статусам')
    statuses = [x for x in collection.find({"type": "status"}) if x.get("timestamp").date() == date.today()]
    for status in statuses:
        bot.reply_to(message, ollama.generate(model=MODEL, system=STATUS, think = False, prompt=status.get("project_name") + status.get("text")).response)

@bot.message_handler(commands=['summary'])
def summary(message):
    scheduled_summary(message.chat.id)

@bot.message_handler(commands=['clear'])
def clear(message):
    chat_id = message.chat.id
    collection.delete_many({})
    bot.send_message(chat_id, 'База данных очищена')

@bot.message_handler(content_types=['text'])
def handle_message(message):
    text = message.text
    if '#статус' in text.lower():
        process_status(text, message)
    elif '#отчет' in text.lower():
        process_report(text, message)

def process_status(text, message):
    project_name = extract_project_name(text)
    if not(collection.find_one({"type": "status", "project_name":project_name})):
        collection.update_one(
            {
                "type": "status",
                "project_name": project_name,
                "timestamp": datetime.fromtimestamp(message.date)
            },
            {
                "$set": {
                    "timestamp": datetime.fromtimestamp(message.date),
                    "text": text
                }
            },
            upsert=True
        )

def process_report(text, message):
    project_name = extract_project_name(text)
    collection.insert_one({
        "type":"report",
        "project_name": project_name,
        "timestamp": datetime.fromtimestamp(message.date),
        "text": text
    })
def extract_project_name(text):
    return ollama.generate(model = MODEL, system = EXTRACT_TITLE, prompt=text, think=False, options={'temperature': 0.0, 'num_predict': 30}).response

def scheduled_summary(chat_id = CHAT_ID):
    bot.send_message(chat_id, 'Начинаю подведение итогов')
    statuses = [x for x in collection.find({"type": "status"}) if x.get("timestamp").date() == date.today()]
    reports = [x for x in collection.find({"type": "report"}) if x.get("timestamp").date() == date.today()]
    for status in statuses:
        bot.send_message(chat_id, ollama.generate(model=MODEL, system=SUMMARIZATION, think=False,
                                              prompt=status.get("project_name") + "\n" + status.get("text") + "\n" +
                                              "\n\n".join([x.get("text") for x in reports if x.get("project_name") == status.get( "project_name")])).response)
scheduler = BackgroundScheduler(timezone=pytz.timezone("Europe/Moscow"))
scheduler.add_job(scheduled_summary, 'cron', hour=12, minute=18)
scheduler.start()
bot.infinity_polling()



