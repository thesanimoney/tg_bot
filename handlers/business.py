import logging

from aiogram import Bot, Router
from aiogram.types import BusinessConnection

logger = logging.getLogger(__name__)
router = Router()

# Track active business connections: {connection_id: BusinessConnection}
active_connections: dict[str, BusinessConnection] = {}


@router.business_connection()
async def handle_business_connection(update: BusinessConnection, bot: Bot) -> None:
    logger.info(f"[handle_business_connection] id={update.id}, user={update.user.id}, enabled={update.is_enabled}, can_reply={update.can_reply}")
    if update.is_enabled:
        active_connections[update.id] = update
        logger.info(
            f"Business connection established: id={update.id}, "
            f"user_id={update.user.id}, can_reply={update.can_reply}"
        )
    else:
        active_connections.pop(update.id, None)
        logger.info(f"Business connection removed: id={update.id}, user_id={update.user.id}")
