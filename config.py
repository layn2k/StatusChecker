import os
from dotenv import load_dotenv
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL = os.getenv("MODEL")
DB = os.getenv("DB")
CHAT_ID = os.getenv("CHAT_ID")
