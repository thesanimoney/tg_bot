import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB OpenAI limit
TRANSCRIPTION_TIMEOUT = 60  # seconds
