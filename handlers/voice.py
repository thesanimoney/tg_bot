import asyncio
import logging
import subprocess
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from config import MAX_FILE_SIZE
from services.transcriber import transcribe_audio, transcribe_audio_stream

logger = logging.getLogger(__name__)
router = Router()


# --- Regular message handlers ---

@router.message(F.voice, ~F.business_connection_id)
async def handle_voice(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_voice] from user={message.from_user.id}, chat={message.chat.id}")
    await _process_audio(message, bot, message.voice.file_id, message.voice.file_size, message.voice.duration, "voice.ogg", "audio/ogg")


@router.message(F.audio, ~F.business_connection_id)
async def handle_audio(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_audio] from user={message.from_user.id}, chat={message.chat.id}")
    audio = message.audio
    ext = audio.file_name.rsplit(".", 1)[-1] if audio.file_name else "mp3"
    mime = audio.mime_type or "audio/mpeg"
    await _process_audio(message, bot, audio.file_id, audio.file_size, audio.duration, f"audio.{ext}", mime)


@router.message(F.video_note, ~F.business_connection_id)
async def handle_video_note(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_video_note] from user={message.from_user.id}, chat={message.chat.id}")
    vn = message.video_note
    await _process_audio(message, bot, vn.file_id, vn.file_size, vn.duration, "video_note.mp4", "video/mp4", is_video=True)


@router.message(F.video, ~F.business_connection_id)
async def handle_video(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_video] from user={message.from_user.id}, chat={message.chat.id}")
    v = message.video
    await _process_audio(message, bot, v.file_id, v.file_size, v.duration, "video.mp4", v.mime_type or "video/mp4", is_video=True)


@router.message(F.document, ~F.business_connection_id)
async def handle_audio_document(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_audio_document] from user={message.from_user.id}, chat={message.chat.id}, mime={message.document.mime_type}")
    doc = message.document
    if not doc.mime_type or not doc.mime_type.startswith("audio/"):
        return
    ext = doc.file_name.rsplit(".", 1)[-1] if doc.file_name else "ogg"
    await _process_audio(message, bot, doc.file_id, doc.file_size, None, f"audio.{ext}", doc.mime_type)


# --- Business message handlers ---

@router.business_message(F.voice)
async def handle_business_voice(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_business_voice] from user={message.from_user.id}, chat={message.chat.id}, biz_conn={message.business_connection_id}")
    if _is_from_bot(message, bot):
        return
    await _process_audio(message, bot, message.voice.file_id, message.voice.file_size, message.voice.duration, "voice.ogg", "audio/ogg")


@router.business_message(F.audio)
async def handle_business_audio(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_business_audio] from user={message.from_user.id}, chat={message.chat.id}, biz_conn={message.business_connection_id}")
    if _is_from_bot(message, bot):
        return
    audio = message.audio
    ext = audio.file_name.rsplit(".", 1)[-1] if audio.file_name else "mp3"
    mime = audio.mime_type or "audio/mpeg"
    await _process_audio(message, bot, audio.file_id, audio.file_size, audio.duration, f"audio.{ext}", mime)


@router.business_message(F.video_note)
async def handle_business_video_note(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_business_video_note] from user={message.from_user.id}, chat={message.chat.id}, biz_conn={message.business_connection_id}")
    if _is_from_bot(message, bot):
        return
    vn = message.video_note
    await _process_audio(message, bot, vn.file_id, vn.file_size, vn.duration, "video_note.mp4", "video/mp4", is_video=True)


@router.business_message(F.video)
async def handle_business_video(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_business_video] from user={message.from_user.id}, chat={message.chat.id}, biz_conn={message.business_connection_id}")
    if _is_from_bot(message, bot):
        return
    v = message.video
    await _process_audio(message, bot, v.file_id, v.file_size, v.duration, "video.mp4", v.mime_type or "video/mp4", is_video=True)


@router.business_message(F.document)
async def handle_business_audio_document(message: Message, bot: Bot) -> None:
    logger.info(f"[handle_business_audio_document] from user={message.from_user.id}, chat={message.chat.id}, biz_conn={message.business_connection_id}")
    if _is_from_bot(message, bot):
        return
    doc = message.document
    if not doc.mime_type or not doc.mime_type.startswith("audio/"):
        return
    ext = doc.file_name.rsplit(".", 1)[-1] if doc.file_name else "ogg"
    await _process_audio(message, bot, doc.file_id, doc.file_size, None, f"audio.{ext}", doc.mime_type)


# --- Shared logic ---

def _is_from_bot(message: Message, bot: Bot) -> bool:
    if message.from_user and message.from_user.id == bot.id:
        logger.info(f"[_is_from_bot] ignoring own message in chat={message.chat.id}")
        return True
    return False


async def _process_audio(
    message: Message,
    bot: Bot,
    file_id: str,
    file_size: int | None,
    duration: int | None,
    filename: str,
    mime_type: str,
    is_video: bool = False,
) -> None:
    chat_id = message.chat.id
    biz_conn_id = message.business_connection_id

    if file_size and file_size > MAX_FILE_SIZE:
        await message.reply("File too large (>25MB). Cannot transcribe.")
        return

    try:
        await bot.send_chat_action(
            chat_id, ChatAction.TYPING,
            business_connection_id=biz_conn_id,
        )

        file = await bot.get_file(file_id)
        buffer: BytesIO = await bot.download_file(file.file_path)

        if is_video:
            buffer = await _extract_audio_from_video(buffer)
            filename = "audio.ogg"
            mime_type = "audio/ogg"

        user_id = message.from_user.id if message.from_user else None
        logger.info(f"Transcribing: chat_id={chat_id}, user_id={user_id}, file_size={file_size}, duration={duration}, business={biz_conn_id is not None}")

        sender_name = message.from_user.first_name if message.from_user else "Unknown"
        prefix = f"<i>{sender_name}</i>:\n"

        # Stream with live message editing
        full_text = ""
        last_edit_text = ""
        min_edit_interval = 1  # seconds between edits to avoid rate limits
        last_edit_time = 0.0

        async def _send(text: str) -> Message:
            return await bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_to_message_id=message.message_id,
                business_connection_id=biz_conn_id,
            )

        async def _edit(msg: Message, text: str) -> None:
            await bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=msg.message_id,
                parse_mode="HTML",
                business_connection_id=biz_conn_id,
            )

        # Send immediate "listening..." message
        reply_msg = await _send("🎧 Listening...")

        try:
            async for delta in transcribe_audio_stream(buffer, filename, mime_type):
                full_text += delta
                now = asyncio.get_event_loop().time()

                if now - last_edit_time >= min_edit_interval and full_text != last_edit_text:
                    await _edit(reply_msg, prefix + full_text)
                    last_edit_text = full_text
                    last_edit_time = now

            # Final edit with complete text
            if full_text:
                if full_text != last_edit_text:
                    await _edit(reply_msg, prefix + full_text)
            else:
                await _edit(reply_msg, "Could not transcribe — audio may be empty or unclear")

        except Exception as e:
            logger.warning(f"Streaming edit failed ({e}), using fallback")
            buffer.seek(0)
            text = await transcribe_audio(buffer, filename, mime_type)
            if not text:
                reply_text = "Could not transcribe — audio may be empty or unclear"
            else:
                reply_text = prefix + text
            await _edit(reply_msg, reply_text)

        buffer.close()

        if not full_text and reply_msg:
            await reply_msg.edit_text("Could not transcribe — audio may be empty or unclear")

    except Exception as e:
        user_id = message.from_user.id if message.from_user else None
        logger.error(f"Transcription failed: chat_id={chat_id}, user_id={user_id}, file_id={file_id}, error={e}")
        await message.reply("Transcription failed. Please try again later.")



async def _extract_audio_from_video(video_buffer: BytesIO) -> BytesIO:
    import tempfile, os
    tmp_in = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_out = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    tmp_in.write(video_buffer.read())
    tmp_in.close()
    tmp_out.close()
    video_buffer.close()

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", tmp_in.name, "-vn", "-acodec", "libopus", tmp_out.name,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"ffmpeg failed: {stderr.decode()}")
        os.unlink(tmp_in.name)
        os.unlink(tmp_out.name)
        raise Exception("ffmpeg audio extraction failed")

    with open(tmp_out.name, "rb") as f:
        result = BytesIO(f.read())

    os.unlink(tmp_in.name)
    os.unlink(tmp_out.name)
    return result
