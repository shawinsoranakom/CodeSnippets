def test_put(client: TestClient, mod: ModuleType):
    fake_db = mod.fake_db

    response = client.put(
        "/items/123",
        json={
            "title": "Foo",
            "timestamp": "2023-01-01T12:00:00",
            "description": "An optional description",
        },
    )
    assert response.status_code == 200
    assert "123" in fake_db
    assert fake_db["123"] == {
        "title": "Foo",
        "timestamp": "2023-01-01T12:00:00",
        "description": "An optional description",
    }