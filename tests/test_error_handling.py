from io import BytesIO

from app.models.domain import User


def test_invalid_email_returns_json_validation_error(client) -> None:
    response = client.post(
        "/users",
        json={"username": "broken-user", "email": "not-an-email"},
    )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert any("email" in error["loc"] for error in body["detail"])


def test_wrong_upload_type_returns_json_error(client) -> None:
    response = client.post(
        "/users/bulk",
        files={"file": ("users.txt", BytesIO(b"not,csv"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only CSV files allowed"}


def test_missing_owner_returns_json_404(client) -> None:
    response = client.post(
        "/urls",
        json={
            "user_id": 9999,
            "original_url": "https://example.com/missing-owner",
            "title": "Missing Owner",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_unknown_route_returns_json_404(client) -> None:
    response = client.get("/not-a-real-route")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_unexpected_error_returns_json_500(resilient_client, db_session, monkeypatch) -> None:
    user = User(username="failing-owner", email="failing-owner@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    def raise_runtime_error(_db):
        raise RuntimeError("simulated crash")

    monkeypatch.setattr("app.routes.urls.generate_short_code", raise_runtime_error)

    response = resilient_client.post(
        "/urls",
        json={
            "user_id": user.id,
            "original_url": "https://example.com/will-fail",
            "title": "Will Fail",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
