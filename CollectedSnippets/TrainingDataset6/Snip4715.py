def test_put_invalid_data(client: TestClient, mod: ModuleType):
    fake_db = mod.fake_db

    response = client.put(
        "/items/345",
        json={
            "title": "Foo",
            "timestamp": "not a date",
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "timestamp"],
                "msg": "Input should be a valid datetime or date, invalid character in year",
                "type": "datetime_from_date_parsing",
                "input": "not a date",
                "ctx": {"error": "invalid character in year"},
            }
        ]
    }
    assert "345" not in fake_db