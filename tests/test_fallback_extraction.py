from app.ai.fallback import classify, extract_fields, heuristic_reply
from app.ai.prompts import GREETING_MESSAGE


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


def test_heuristic_reply_remembers_a_historical_bare_number_answer():
    # Regression: a bare "2" answering the rooms question several turns ago
    # used to be forgotten on later turns (the re-scan of history couldn't
    # tell it was answering "rooms" without knowing what was asked at the
    # time), so the bot re-asked "Скільки кімнат потрібно?" after every
    # subsequent answer instead of moving on.
    history = [
        {"role": "assistant", "content": "Скільки кімнат потрібно?"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "Залиште, будь ласка, номер телефону для зв'язку."},
    ]
    result = heuristic_reply(history, "0501234567")
    assert "кімнат" not in result.reply_text.lower()


def test_heuristic_reply_does_not_misread_its_own_greeting_as_an_answer():
    # Regression: the greeting itself asks "купівля, оренда чи продаж?",
    # which used to be re-scanned as if the client had said it, making the
    # bot think deal_type (and everything else) was already known after a
    # single real answer, and jump straight to "Зараз підберу варіанти".
    history = [{"role": "assistant", "content": GREETING_MESSAGE}]
    result = heuristic_reply(history, "купівля")
    assert result.profile_updates["deal_type"] == "buy"
    assert "міст" in result.reply_text.lower()
    assert "зараз підберу" not in result.reply_text.lower()
