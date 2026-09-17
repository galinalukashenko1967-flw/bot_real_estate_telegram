from __future__ import annotations

from typing import Any

from app.models import DealType, Lead, PropertyType, Temperature

_VALID_DEAL_TYPES = {item.value for item in DealType}
_VALID_PROPERTY_TYPES = {item.value for item in PropertyType}
_VALID_TEMPERATURES = {item.value for item in Temperature}


def apply_profile_updates(lead: Lead, updates: dict[str, Any]) -> None:
    """Apply AI-extracted profile fields onto a Lead, validating enum
    values so a stray/unexpected value from the model never corrupts the
    lead record."""

    if "deal_type" in updates and updates["deal_type"] in _VALID_DEAL_TYPES:
        lead.deal_type = DealType(updates["deal_type"])
    if "property_type" in updates and updates["property_type"] in _VALID_PROPERTY_TYPES:
        lead.property_type = PropertyType(updates["property_type"])
    if "city" in updates and updates["city"]:
        lead.city = str(updates["city"]).strip()
    if "district" in updates and updates["district"]:
        lead.district = str(updates["district"]).strip()
    if "rooms" in updates and updates["rooms"]:
        lead.rooms = int(updates["rooms"])
    if "budget_min" in updates and updates["budget_min"]:
        lead.budget_min = int(updates["budget_min"])
    if "budget_max" in updates and updates["budget_max"]:
        lead.budget_max = int(updates["budget_max"])
    if "budget_currency" in updates and updates["budget_currency"]:
        lead.budget_currency = str(updates["budget_currency"])
    if "phone" in updates and updates["phone"]:
        lead.phone = str(updates["phone"]).strip()
    if "full_name" in updates and updates["full_name"]:
        lead.full_name = str(updates["full_name"]).strip()


def apply_classification(lead: Lead, classification: dict[str, Any] | None) -> None:
    if not classification:
        return
    temperature = classification.get("temperature")
    if temperature in _VALID_TEMPERATURES:
        lead.temperature = Temperature(temperature)
    urgency = classification.get("urgency")
    if urgency:
        lead.urgency = str(urgency)


def heuristic_classification(lead: Lead) -> Temperature:
    """Fallback rule-based qualification used when the AI hasn't produced an
    explicit classification yet: a lead with all core criteria plus a phone
    number is at least warm; missing the phone or budget keeps it cold."""

    if lead.is_qualified():
        return Temperature.WARM
    if lead.phone and (lead.budget_max or lead.budget_min):
        return Temperature.WARM
    return Temperature.COLD
