import asyncio
import logging
import os
import re
import tempfile

logger = logging.getLogger(__name__)

VIDEO_URL_PATTERNS = [
    # Instagram reels/posts/tv
    re.compile(r"https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[\w-]+/?(?:\?[^\s]*)?"),
    # TikTok
    re.compile(r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+(?:\?[^\s]*)?"),
    re.compile(r"https?://(?:vm|vt)\.tiktok\.com/[\w-]+/?(?:\?[^\s]*)?"),
    # YouTube Shorts
    re.compile(r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+(?:\?[^\s]*)?"),
    re.compile(r"https?://youtu\.be/[\w-]+(?:\?[^\s]*)?"),
]


def extract_video_url(text: str) -> str | None:
    """Extract supported video URL from text."""
    for pattern in VIDEO_URL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


async def download_video(url: str) -> str | None:
    """Download video using yt-dlp. Returns path to downloaded file."""
    tmp_dir = tempfile.mkdtemp(prefix="vid_")
    output_path = os.path.join(tmp_dir, "video.mp4")

    logger.info(f"[video_dl] Downloading: {url}")

    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "--no-warnings",
        "--no-playlist",
        "--max-filesize", "50M",
        "-f", "mp4/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"[video_dl] yt-dlp failed: {stderr.decode()}")
        _cleanup(tmp_dir)
        return None

    if not os.path.exists(output_path):
        for f in os.listdir(tmp_dir):
            if f.endswith(".mp4"):
                output_path = os.path.join(tmp_dir, f)
                break
        else:
            logger.error(f"[video_dl] No mp4 file found in {tmp_dir}")
            _cleanup(tmp_dir)
            return None

    file_size = os.path.getsize(output_path)
    logger.info(f"[video_dl] Downloaded: {output_path} ({file_size} bytes)")
    return output_path


def cleanup_file(path: str) -> None:
    """Remove downloaded file and its directory."""
    try:
        tmp_dir = os.path.dirname(path)
        os.remove(path)
        os.rmdir(tmp_dir)
    except OSError:
        pass


def _cleanup(tmp_dir: str) -> None:
    try:
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)
    except OSError:
        pass
