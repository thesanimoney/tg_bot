import logging
import re

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message) -> None:
    logger.info(f"[cmd_start_deep_link] from user={message.from_user.id}, chat={message.chat.id}, text={message.text}")
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        match = re.match(r"bizChat(\d+)", args[1])
        if match:
            user_chat_id = match.group(1)
            await message.reply(
                f"<b>Managing business chat</b>\n\n"
                f"Chat ID: <code>{user_chat_id}</code>\n\n"
                f"I'll automatically transcribe voice messages and audio files "
                f"in your business chats.",
                parse_mode="HTML",
            )
            return

    await _send_start(message)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    logger.info(f"[cmd_start] from user={message.from_user.id}, chat={message.chat.id}")
    await _send_start(message)


async def _send_start(message: Message) -> None:
    await message.reply(
        "<b>Voice Transcription Bot</b>\n\n"
        "I automatically transcribe voice messages, audio files, and video notes.\n\n"
        "<b>Business Mode:</b>\n"
        "Connect me via Telegram Business settings to auto-transcribe "
        "voice messages in your business chats.\n\n"
        "<b>Commands:</b>\n"
        "/start — Show this message",
        parse_mode="HTML",
    )
