from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.ai.prompts import GREETING_MESSAGE, UNSUPPORTED_CITY_NOTE
from app.bot.formatting import (
    format_lead_summary_for_realtor,
    format_property_card,
    format_reaction_confirmation,
)
from app.bot.keyboards import parse_reaction_callback, property_reaction_keyboard
from app.bot.notifications import notify_realtor
from app.config import get_settings
from app.db import async_session_factory
from app.models import Property
from app.search.hybrid import hybrid_search
from app.services.leads import get_or_create_lead, handle_incoming_message, record_reaction

logger = logging.getLogger(__name__)
router = Router(name="lead_dialogue")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        if not lead.conversation_history:
            lead.conversation_history = [{"role": "assistant", "content": GREETING_MESSAGE}]
        await session.commit()

    await message.answer(GREETING_MESSAGE)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, bot: Bot) -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        was_qualified = lead.is_qualified()

        result = await handle_incoming_message(session, lead, message.text)
        await message.answer(result.reply_text)

        if lead.city and lead.city not in settings.rieltor_ua_allowed_cities_list:
            await message.answer(UNSUPPORTED_CITY_NOTE)

        should_search = lead.is_qualified() and not was_qualified

        if should_search:
            properties = await hybrid_search(session, lead)
            await session.commit()

            if not properties:
                await message.answer(
                    "На жаль, зараз немає варіантів під ваш запит. Рієлтор зв'яжеться "
                    "з вами, щойно з'явиться щось відповідне."
                )
            else:
                await message.answer(f"Знайшов {len(properties)} варіант(и) під ваш запит:")
                for prop in properties:
                    await message.answer(
                        format_property_card(prop),
                        reply_markup=property_reaction_keyboard(prop),
                        parse_mode="HTML",
                        disable_web_page_preview=False,
                    )
            await notify_realtor(bot, format_lead_summary_for_realtor(lead))
        else:
            await session.commit()


@router.callback_query(F.data.startswith("react:"))
async def handle_reaction(callback: CallbackQuery, bot: Bot) -> None:
    property_id, reaction = parse_reaction_callback(callback.data)

    async with async_session_factory() as session:
        lead = await get_or_create_lead(
            session,
            telegram_user_id=callback.from_user.id,
            telegram_username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )
        property_ = await session.get(Property, property_id)
        if property_ is None:
            await callback.answer("Це оголошення більше недоступне.", show_alert=True)
            return

        await record_reaction(session, lead, property_, reaction)
        await session.commit()

        confirmation_text = format_reaction_confirmation(property_, reaction)

    await callback.message.edit_text(confirmation_text, parse_mode="HTML")
    await callback.answer("Записав вашу реакцію!")

    realtor_note = (
        f"📩 Реакція клієнта {callback.from_user.full_name}: "
        f"{reaction.value} — {property_.title}"
    )
    await notify_realtor(bot, realtor_note)
