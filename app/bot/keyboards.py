from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models import Property, ReactionType

REACTION_LABELS = {
    ReactionType.INTERESTED: "👍 Зацікавило",
    ReactionType.WANT_VIEWING: "📅 Хочу перегляд",
    ReactionType.NOT_SUITABLE: "👎 Не підійшло",
}


def reaction_callback_data(property_id: int, reaction: ReactionType) -> str:
    return f"react:{property_id}:{reaction.value}"


def parse_reaction_callback(data: str) -> tuple[int, ReactionType]:
    _, property_id, reaction_value = data.split(":")
    return int(property_id), ReactionType(reaction_value)


def property_reaction_keyboard(property_: Property) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=label, callback_data=reaction_callback_data(property_.id, reaction)
        )
        for reaction, label in REACTION_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
