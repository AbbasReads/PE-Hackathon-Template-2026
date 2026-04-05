from app.utils import generate_short_code, parse_users_csv


def test_parse_users_csv_keeps_only_complete_rows() -> None:
    file_content = """username,email
alice,alice@example.com
bob,
,charlie@example.com
dana,dana@example.com
"""

    users = parse_users_csv(file_content)

    assert users == [
        {"username": "alice", "email": "alice@example.com"},
        {"username": "dana", "email": "dana@example.com"},
    ]


def test_parse_users_csv_deduplicates_case_insensitive_emails_and_strips_values() -> None:
    file_content = """username,email
 Alice ,ALICE@example.com
alice-dup,alice@example.com
 Bob , bob@example.com 
"""

    users = parse_users_csv(file_content)

    assert users == [
        {"username": "Alice", "email": "alice@example.com"},
        {"username": "Bob", "email": "bob@example.com"},
    ]


def test_parse_users_csv_rejects_extra_columns_as_malformed() -> None:
    file_content = "username,email\nalice,alice@example.com,unexpected\n"

    try:
        parse_users_csv(file_content)
    except ValueError as exc:
        assert str(exc) == "Malformed CSV data"
    else:
        raise AssertionError("Expected malformed CSV data to raise ValueError")


def test_generate_short_code_retries_until_unique(monkeypatch) -> None:
    generated_codes = iter([list("ABC123"), list("XYZ789")])

    class FakeQuery:
        def __init__(self) -> None:
            self.seen_calls = 0

        def filter(self, *_args, **_kwargs):
            self.seen_calls += 1
            return self

        def first(self):
            if self.seen_calls == 1:
                return object()
            return None

    class FakeDB:
        def __init__(self) -> None:
            self.query_result = FakeQuery()

        def query(self, _model):
            return self.query_result

    monkeypatch.setattr("app.utils.random.choices", lambda *_args, **_kwargs: next(generated_codes))

    short_code = generate_short_code(FakeDB())

    assert short_code == "XYZ789"
