from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, Property, PropertySource, Reaction, ReactionType


async def search_internal_properties(
    session: AsyncSession, lead: Lead, limit: int = 5
) -> list[Property]:
    """Search the in-house property database for offers matching the lead's
    criteria, excluding anything the lead has already marked as
    'not suitable' (permanent exclusion, per the reaction-history rule)."""

    excluded_ids_subquery = (
        select(Reaction.property_id)
        .where(Reaction.lead_id == lead.id)
        .where(Reaction.reaction == ReactionType.NOT_SUITABLE)
    )

    query = select(Property).where(
        Property.source == PropertySource.INTERNAL,
        Property.id.not_in(excluded_ids_subquery),
    )

    if lead.deal_type:
        query = query.where(Property.deal_type == lead.deal_type)
    if lead.city:
        query = query.where(Property.city == lead.city)
    if lead.property_type:
        query = query.where(Property.property_type == lead.property_type)
    if lead.rooms:
        query = query.where(Property.rooms == lead.rooms)
    if lead.budget_max:
        query = query.where(Property.price <= lead.budget_max)
    if lead.budget_min:
        query = query.where(Property.price >= lead.budget_min)

    query = query.order_by(Property.created_at.desc()).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())
