# Telegram Voice Transcription Bot

Automatically transcribes voice messages, audio files, and video notes using OpenAI's `gpt-4o-transcribe` model.

## Prerequisites

- Python 3.11+
- ffmpeg (`brew install ffmpeg` on macOS)
- Telegram bot token (from [@BotFather](https://t.me/BotFather))
- OpenAI API key

## BotFather Setup

1. `/newbot` — create bot, save token
2. `/setprivacy` — select bot — **Disable** (so bot sees all messages in groups)
3. `/setcommands` — set:
   ```
   start - Show usage
   allow - Allow this chat
   deny - Deny this chat
   ```
4. Add bot to target chats as admin (alternative to disabling privacy mode)

## Get Your User ID

Forward any message to [@userinfobot](https://t.me/userinfobot) to get your numeric user ID.

## Configuration

Copy `.env.example` to `.env` and fill in:

```env
TELEGRAM_BOT_TOKEN=<from BotFather>
OPENAI_API_KEY=<your key>
OWNER_USER_ID=<your numeric Telegram user ID>
ALLOWED_CHAT_IDS=<optional comma-separated chat IDs>
TRANSCRIPTION_MODEL=gpt-4o-transcribe
LOG_LEVEL=INFO
```

## Run Locally

```bash
pip install -r requirements.txt
python main.py
```

## Docker

```bash
docker build -t stt-bot .
docker run --env-file .env stt-bot
```

## Cost

gpt-4o-transcribe: ~$0.006/minute of audio.
# tg_bot
