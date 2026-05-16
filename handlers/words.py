import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter
from aiogram.types import Message, ReactionTypeEmoji

logger = logging.getLogger(__name__)
router = Router()

# word -> response (matched case-insensitively)
WORD_RESPONSES: dict[str, str] = {
    "плачу": "поцілуй пізду собачу",
}

BOT_EMOJI = "🤖"
THINKING_TEXT = "Думаю що тобі умніку відповісти..."
THINKING_DELAY = 0.7


class WordMatchFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict:
        if not message.text:
            return False
        lower = message.text.strip().lower()
        response = WORD_RESPONSES.get(lower)
        if response:
            return {"word_response": response}
        return False


async def _respond(message: Message, bot: Bot, response: str) -> None:
    chat_id = message.chat.id
    biz_conn_id = message.business_connection_id

    msg = await bot.send_message(
        chat_id,
        f"{BOT_EMOJI} STT Bot:\n{THINKING_TEXT}",
        reply_to_message_id=message.message_id,
        business_connection_id=biz_conn_id,
    )

    await asyncio.sleep(THINKING_DELAY)

    await bot.edit_message_text(
        f"{BOT_EMOJI} STT Bot:\n{response}",
        chat_id=chat_id,
        message_id=msg.message_id,
        business_connection_id=biz_conn_id,
    )

    await bot.set_message_reaction(
        chat_id,
        message.message_id,
        reaction=[ReactionTypeEmoji(emoji=BOT_EMOJI)],
        **({"business_connection_id": biz_conn_id} if biz_conn_id else {}),
    )


@router.message(WordMatchFilter(), ~F.business_connection_id)
async def handle_word(message: Message, bot: Bot, word_response: str) -> None:
    logger.info(f"[words] Matched '{message.text}' from user={message.from_user.id}, chat={message.chat.id}")
    await _respond(message, bot, word_response)


@router.business_message(WordMatchFilter())
async def handle_business_word(message: Message, bot: Bot, word_response: str) -> None:
    if message.from_user and message.from_user.id == bot.id:
        return
    logger.info(f"[words] Matched business '{message.text}' from user={message.from_user.id}, chat={message.chat.id}")
    await _respond(message, bot, word_response)
