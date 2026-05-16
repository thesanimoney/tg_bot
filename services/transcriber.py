import asyncio
import logging
from collections.abc import AsyncGenerator
from io import BytesIO
from openai import AsyncOpenAI, APIStatusError
from config import OPENAI_API_KEY, TRANSCRIPTION_MODEL, TRANSCRIPTION_TIMEOUT

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio_stream(buffer: BytesIO, filename: str = "voice.ogg", mime_type: str = "audio/ogg") -> AsyncGenerator[str, None]:
    """Stream transcription deltas. Yields text chunks as they arrive."""
    buffer.seek(0)
    file_size = buffer.getbuffer().nbytes
    logger.info(f"[transcribe] REQUEST: model={TRANSCRIPTION_MODEL}, filename={filename}, mime_type={mime_type}, file_size={file_size} bytes, stream=True")

    response = await client.audio.transcriptions.create(
        model=TRANSCRIPTION_MODEL,
        file=(filename, buffer, mime_type),
        response_format="text",
        stream=True,
    )
    async for event in response:
        logger.debug(f"[transcribe] stream event: type={type(event).__name__}, attrs={vars(event) if hasattr(event, '__dict__') else event}")
        if hasattr(event, "delta") and event.delta:
            yield event.delta


async def transcribe_audio(buffer: BytesIO, filename: str = "voice.ogg", mime_type: str = "audio/ogg") -> str:
    """Transcribe audio buffer (non-streaming fallback)."""
    buffer.seek(0)
    file_size = buffer.getbuffer().nbytes
    logger.info(f"[transcribe] REQUEST (fallback): model={TRANSCRIPTION_MODEL}, filename={filename}, mime_type={mime_type}, file_size={file_size} bytes")

    result = await client.audio.transcriptions.create(
        model=TRANSCRIPTION_MODEL,
        file=(filename, buffer, mime_type),
        response_format="text",
    )
    if isinstance(result, str):
        text = result.strip()
    else:
        text = result.text.strip() if hasattr(result, "text") else str(result).strip()
    logger.info(f"[transcribe] RESPONSE (fallback): length={len(text)} chars, text={text[:200]!r}")
    return text
