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


def test_heuristic_reply_understands_bare_number_answering_rooms_question():
    # Regression: a bare "2" in reply to "Скільки кімнат потрібно?" used to be
    # silently dropped, so the bot re-asked the same question forever.
    history = [{"role": "assistant", "content": "Скільки кімнат потрібно?"}]
    result = heuristic_reply(history, "2")
    assert result.profile_updates["rooms"] == 2
    assert "кімнат" not in result.reply_text.lower()


def test_heuristic_reply_understands_bare_number_answering_budget_question():
    history = [{"role": "assistant", "content": "Який орієнтовний бюджет?"}]
    result = heuristic_reply(history, "90000")
    assert result.profile_updates["budget_max"] == 90000


def test_heuristic_reply_ignores_bare_number_with_no_pending_question():
    result = heuristic_reply([], "2")
    assert "rooms" not in result.profile_updates
    assert "budget_max" not in result.profile_updates
