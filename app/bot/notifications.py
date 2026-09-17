from __future__ import annotations

import logging

from aiogram import Bot

from app.config import get_settings

logger = logging.getLogger(__name__)


async def notify_realtor(bot: Bot, text: str) -> None:
    settings = get_settings()
    if not settings.realtor_chat_id:
        logger.debug("REALTOR_CHAT_ID not configured, skipping realtor notification")
        return
    try:
        await bot.send_message(settings.realtor_chat_id, text, parse_mode="HTML")
    except Exception:  # noqa: BLE001 - notification best-effort, never break the flow
        logger.warning("Failed to notify realtor", exc_info=True)
