import logging

from aiogram import Bot, F, Router
from aiogram.types import FSInputFile, Message

from services.video_downloader import (
    cleanup_file,
    download_video,
    extract_video_url,
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text, ~F.business_connection_id)
async def handle_video_link(message: Message, bot: Bot) -> None:
    if not message.text:
        return
    url = extract_video_url(message.text)
    if not url:
        return

    logger.info(f"[video_dl] Detected link from user={message.from_user.id}, chat={message.chat.id}, url={url}")
    await _process_video(message, bot, url)


@router.business_message(F.text)
async def handle_business_video_link(message: Message, bot: Bot) -> None:
    if not message.text:
        return
    if message.from_user and message.from_user.id == bot.id:
        return
    url = extract_video_url(message.text)
    if not url:
        return

    logger.info(f"[video_dl] Detected business link from user={message.from_user.id}, chat={message.chat.id}, url={url}")
    await _process_video(message, bot, url)


async def _process_video(message: Message, bot: Bot, url: str) -> None:
    chat_id = message.chat.id
    biz_conn_id = message.business_connection_id

    status_msg = await bot.send_message(
        chat_id,
        "📥 Downloading video...",
        reply_to_message_id=message.message_id,
        business_connection_id=biz_conn_id,
    )

    try:
        path = await download_video(url)

        if not path:
            await bot.edit_message_text(
                "Failed to download video.",
                chat_id=chat_id,
                message_id=status_msg.message_id,
                business_connection_id=biz_conn_id,
            )
            return

        await bot.edit_message_text(
            "📤 Sending video...",
            chat_id=chat_id,
            message_id=status_msg.message_id,
            business_connection_id=biz_conn_id,
        )

        video_file = FSInputFile(path)
        await bot.send_video(
            chat_id,
            video=video_file,
            reply_to_message_id=message.message_id,
            business_connection_id=biz_conn_id,
        )

        await bot.edit_message_text(
            "✅ Video sent",
            chat_id=chat_id,
            message_id=status_msg.message_id,
            business_connection_id=biz_conn_id,
        )

        cleanup_file(path)

    except Exception as e:
        logger.error(f"[video_dl] Failed: chat={chat_id}, url={url}, error={e}")
        await bot.edit_message_text(
            "Failed to download video. Please try again.",
            chat_id=chat_id,
            message_id=status_msg.message_id,
            business_connection_id=biz_conn_id,
        )
