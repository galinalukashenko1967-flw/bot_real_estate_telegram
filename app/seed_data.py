"""Populate the internal property inventory with sample listings so the bot
has something to match against out of the box. Run with:

    python -m app.seed_data
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db import async_session_factory, init_db
from app.models import DealType, Property, PropertySource, PropertyType

SAMPLE_PROPERTIES = [
    dict(
        title="вул. Володимирська, 2к, 65м²",
        city="Київ",
        district="Шевченківський",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=2,
        area_sqm=65,
        price=95_000,
        currency="USD",
        description="Затишна двокімнатна квартира в центрі, євроремонт.",
    ),
    dict(
        title="пр-т Перемоги, 1к, 42м²",
        city="Київ",
        district="Солом'янський",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=1,
        area_sqm=42,
        price=68_000,
        currency="USD",
        description="Однокімнатна квартира біля метро, новобудова.",
    ),
    dict(
        title="вул. Личаківська, 3к, 88м²",
        city="Львів",
        district="Личаківський",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.BUY,
        rooms=3,
        area_sqm=88,
        price=99_000,
        currency="USD",
        description="Простора трикімнатна квартира з видом на парк.",
    ),
    dict(
        title="вул. Хрещатик, 2к, 55м² в оренду",
        city="Київ",
        district="Печерський",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=2,
        area_sqm=55,
        price=25_000,
        currency="UAH",
        description="Оренда в центрі, повністю мебльована.",
    ),
    dict(
        title="вул. Городоцька, 1к, 38м² в оренду",
        city="Львів",
        district="Залізничний",
        property_type=PropertyType.APARTMENT,
        deal_type=DealType.RENT,
        rooms=1,
        area_sqm=38,
        price=12_000,
        currency="UAH",
        description="Компактна квартира для оренди поруч з центром.",
    ),
    dict(
        title="Будинок в передмісті Києва, 4к, 150м²",
        city="Київ",
        district="Обухівський р-н",
        property_type=PropertyType.HOUSE,
        deal_type=DealType.BUY,
        rooms=4,
        area_sqm=150,
        price=99_500,
        currency="USD",
        description="Будинок з ділянкою 6 соток, готовий до заселення.",
    ),
]


async def seed() -> None:
    await init_db()
    async with async_session_factory() as session:
        existing = await session.execute(
            select(Property).where(Property.source == PropertySource.INTERNAL)
        )
        if existing.scalars().first() is not None:
            print("Internal properties already seeded, skipping.")
            return

        for data in SAMPLE_PROPERTIES:
            session.add(Property(source=PropertySource.INTERNAL, **data))

        await session.commit()
        print(f"Seeded {len(SAMPLE_PROPERTIES)} internal properties.")


if __name__ == "__main__":
    asyncio.run(seed())
