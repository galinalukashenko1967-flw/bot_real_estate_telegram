from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, Property, PropertySource, PropertyType, Reaction, ReactionType
from app.search.internal import search_internal_properties
from app.search.rieltor_ua import fetch_listings


async def _upsert_scraped_properties(session: AsyncSession, lead: Lead) -> list[Property]:
    scraped = await fetch_listings(lead)
    if not scraped:
        return []

    external_ids = [item.external_id for item in scraped]
    existing = await session.execute(
        select(Property).where(
            Property.source == PropertySource.RIELTOR_UA,
            Property.external_id.in_(external_ids),
        )
    )
    existing_by_external_id = {p.external_id: p for p in existing.scalars().all()}

    properties: list[Property] = []
    for item in scraped:
        prop = existing_by_external_id.get(item.external_id)
        if prop is None:
            prop = Property(
                source=PropertySource.RIELTOR_UA,
                external_id=item.external_id,
                deal_type=lead.deal_type,
                property_type=lead.property_type or PropertyType.APARTMENT,
            )
            session.add(prop)
        prop.title = item.title
        prop.city = item.city
        prop.district = item.district
        prop.rooms = item.rooms
        prop.area_sqm = item.area_sqm
        prop.price = item.price
        prop.currency = item.currency
        prop.url = item.url
        properties.append(prop)

    await session.flush()
    return properties


async def hybrid_search(session: AsyncSession, lead: Lead, limit: int = 5) -> list[Property]:
    """Search internal inventory and live RIELTOR.UA listings in parallel
    intent (sequential awaits here, both are fast/best-effort), merge the
    results and filter out anything the lead already marked 'not suitable'."""

    internal_results = await search_internal_properties(session, lead, limit=limit)
    scraped_properties = await _upsert_scraped_properties(session, lead)

    excluded = await session.execute(
        select(Reaction.property_id)
        .where(Reaction.lead_id == lead.id)
        .where(Reaction.reaction == ReactionType.NOT_SUITABLE)
    )
    excluded_ids = {row[0] for row in excluded.all()}

    def matches_budget(prop: Property) -> bool:
        if lead.budget_max and prop.price > lead.budget_max:
            return False
        if lead.budget_min and prop.price < lead.budget_min:
            return False
        return True

    filtered_scraped = [
        p for p in scraped_properties if p.id not in excluded_ids and matches_budget(p)
    ]

    combined = internal_results + filtered_scraped
    seen_ids: set[int] = set()
    unique: list[Property] = []
    for prop in combined:
        if prop.id in seen_ids:
            continue
        seen_ids.add(prop.id)
        unique.append(prop)

    return unique[:limit]
