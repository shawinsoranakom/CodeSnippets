def test_get(client: TestClient):
    response = client.get("/facilities/42")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": "42",
        "address": {
            "line_1": "123 Main St",
            "city": "Anytown",
            "state_province": "CA",
        },
    }