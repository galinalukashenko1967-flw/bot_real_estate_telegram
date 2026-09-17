from app.ai.fallback import classify, extract_fields, heuristic_reply


def test_extract_deal_type_and_city():
    fields = extract_fields("Хочу купити квартиру у Києві")
    assert fields["deal_type"] == "buy"
    assert fields["property_type"] == "apartment"
    assert fields["city"] == "Київ"


def test_extract_rooms_budget_phone():
    fields = extract_fields("Потрібно 2 кімнати, бюджет 95000 usd, телефон +380501234567")
    assert fields["rooms"] == 2
    assert fields["budget_max"] == 95000
    assert fields["budget_currency"] == "USD"
    assert fields["phone"] == "+380501234567"


def test_classify_hot_when_urgent_and_has_core_data():
    fields = {"budget_max": 95000, "phone": "+380501234567"}
    result = classify(fields, "Потрібно терміново, цього тижня")
    assert result["temperature"] == "hot"


def test_classify_cold_without_core_data():
    result = classify({}, "просто дивлюсь варіанти")
    assert result is None


def test_heuristic_reply_asks_for_missing_field():
    result = heuristic_reply([], "Хочу купити квартиру")
    assert result.profile_updates["deal_type"] == "buy"
    assert "місто" in result.reply_text.lower() or "київ" in result.reply_text.lower()
