import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from handlers.business import router as business_router
from handlers.commands import router as commands_router
from handlers.instagram import router as instagram_router
from handlers.voice import router as voice_router
from handlers.words import router as words_router

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    @dp.update.outer_middleware()
    async def log_all_updates(handler, event: Update, data):
        update_type = event.event_type
        user = None
        chat = None
        if event.message:
            user = event.message.from_user
            chat = event.message.chat
        elif event.business_message:
            user = event.business_message.from_user
            chat = event.business_message.chat
        elif event.edited_business_message:
            user = event.edited_business_message.from_user
            chat = event.edited_business_message.chat
        elif event.business_connection:
            user = event.business_connection.user

        user_info = f"user={user.id}(@{user.username})" if user else "user=unknown"
        chat_info = f"chat={chat.id}({chat.type})" if chat else ""
        logger.info(f"UPDATE [{update_type}] {user_info} {chat_info} update_id={event.update_id}")

        return await handler(event, data)

    dp.include_router(business_router)
    dp.include_router(commands_router)
    dp.include_router(words_router)
    dp.include_router(instagram_router)
    dp.include_router(voice_router)

    logger.info("Bot starting...")
    await dp.start_polling(bot, allowed_updates=[
        "message",
        "business_connection",
        "business_message",
    ])


if __name__ == "__main__":
    asyncio.run(main())
