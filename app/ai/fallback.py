"""A minimal rule-based stand-in for the Claude dialogue engine.

Used when ANTHROPIC_API_KEY is not configured, so the bot, the qualification
pipeline and the web cabinet remain testable and runnable end-to-end without
a live LLM key. It intentionally does *not* try to replicate the natural
conversation quality of the real AI agent — only extracts the same
structured fields via simple regular expressions.
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.claude_client import DialogueResult

_DEAL_TYPE_PATTERNS = {
    "rent": re.compile(r"орен|зня(ти|ла)|найм", re.IGNORECASE),
    "sell": re.compile(r"продат|продаж", re.IGNORECASE),
    "buy": re.compile(r"купит|купівл|придбат", re.IGNORECASE),
}

_PROPERTY_TYPE_PATTERNS = {
    "house": re.compile(r"буд(инок|инку)|котедж", re.IGNORECASE),
    "commercial": re.compile(r"комерц|офіс|магазин", re.IGNORECASE),
    "land": re.compile(r"землі|ділянк", re.IGNORECASE),
    "apartment": re.compile(r"квартир", re.IGNORECASE),
}

_CITY_PATTERNS = {
    "Київ": re.compile(r"ки[їє]в|kyiv|kiev", re.IGNORECASE),
    "Львів": re.compile(r"льв[іоа]в|lviv", re.IGNORECASE),
}

_ROOMS_RE = re.compile(r"(\d+)\s*[-]?\s*к(імн|імнат|)")
_PHONE_RE = re.compile(r"(\+?380\d{9}|0\d{9})")
_BUDGET_RE = re.compile(
    r"(?P<amount>\d[\d\s]{2,})\s*(?P<currency>usd|\$|грн|uah|eur|€)?", re.IGNORECASE
)
_URGENT_RE = re.compile(r"термін|швидко|цього тижня|негайно|якнайшвидше", re.IGNORECASE)

_CURRENCY_MAP = {"$": "USD", "usd": "USD", "грн": "UAH", "uah": "UAH", "eur": "EUR", "€": "EUR"}

_QUESTIONS_ORDER = [
    ("deal_type", "Уточніть, будь ласка: купівля, оренда чи продаж?"),
    ("city", "У якому місті шукаємо (Київ чи Львів)?"),
    ("property_type", "Який тип об'єкта цікавить: квартира, будинок, комерція чи земля?"),
    ("rooms", "Скільки кімнат потрібно?"),
    ("budget_max", "Який орієнтовний бюджет?"),
    ("phone", "Залиште, будь ласка, номер телефону для зв'язку."),
]


def extract_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}

    for value, pattern in _DEAL_TYPE_PATTERNS.items():
        if pattern.search(text):
            fields["deal_type"] = value
            break

    for value, pattern in _PROPERTY_TYPE_PATTERNS.items():
        if pattern.search(text):
            fields["property_type"] = value
            break

    for city, pattern in _CITY_PATTERNS.items():
        if pattern.search(text):
            fields["city"] = city
            break

    rooms_match = _ROOMS_RE.search(text)
    if rooms_match:
        fields["rooms"] = int(rooms_match.group(1))

    phone_match = _PHONE_RE.search(text)
    if phone_match:
        fields["phone"] = phone_match.group(1)

    budget_match = _BUDGET_RE.search(text)
    if budget_match and len(budget_match.group("amount").replace(" ", "")) >= 3:
        amount = int(budget_match.group("amount").replace(" ", ""))
        fields["budget_max"] = amount
        currency = budget_match.group("currency")
        if currency:
            fields["budget_currency"] = _CURRENCY_MAP.get(currency.lower(), "USD")

    return fields


def classify(fields: dict[str, Any], text: str) -> dict[str, Any] | None:
    if not fields:
        return None
    has_core = fields.get("budget_max") and fields.get("phone")
    is_urgent = bool(_URGENT_RE.search(text))
    if has_core and is_urgent:
        temperature = "hot"
    elif has_core:
        temperature = "warm"
    else:
        temperature = "cold"
    return {
        "temperature": temperature,
        "urgency": "терміново" if is_urgent else "не вказано",
    }


_BARE_NUMBER_RE = re.compile(r"^\s*(\d+)\s*\+?\s*$")


def _pending_field(conversation_history: list[dict[str, Any]]) -> str | None:
    """Which field the bot's last message asked about, so a bare reply like
    '2' can be understood as answering that specific question instead of
    being silently dropped (and the same question re-asked forever)."""

    for msg in reversed(conversation_history):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        for key, question in _QUESTIONS_ORDER:
            if question in content:
                return key
        return None
    return None


def heuristic_reply(
    conversation_history: list[dict[str, Any]], user_message: str
) -> DialogueResult:
    fields = extract_fields(user_message)

    if not fields:
        bare_number = _BARE_NUMBER_RE.match(user_message)
        if bare_number:
            pending = _pending_field(conversation_history)
            if pending == "rooms":
                fields["rooms"] = int(bare_number.group(1))
            elif pending == "budget_max":
                fields["budget_max"] = int(bare_number.group(1))

    classification = classify(fields, user_message)

    known = dict(fields)
    for msg in conversation_history:
        if msg.get("role") != "user":
            # Only scan the client's own messages: the bot's own questions
            # ("купівля, оренда чи продаж?") contain the same trigger words
            # as real answers and would otherwise be misread as one.
            continue
        content = msg.get("content")
        if isinstance(content, str):
            known.update({k: v for k, v in extract_fields(content).items() if k not in known})

    next_question = None
    for key, question in _QUESTIONS_ORDER:
        if key not in known and key not in fields:
            next_question = question
            break

    if fields:
        reply = "Дякую, записав! "
        reply += next_question or "Зараз підберу варіанти під ваш запит."
    else:
        reply = next_question or "Розкажіть, будь ласка, детальніше про ваш запит."

    history = list(conversation_history) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return DialogueResult(
        reply_text=reply,
        profile_updates=fields,
        classification=classification,
        conversation_history=history,
    )
