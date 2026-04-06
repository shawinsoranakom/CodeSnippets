def test_put_missing_required_in_item(client: TestClient):
    response = client.put(
        "/items/5",
        json={"description": "A very nice Item"},
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "name"],
                "input": {"description": "A very nice Item"},
                "msg": "Field required",
                "type": "missing",
            },
            {
                "loc": ["body", "price"],
                "input": {"description": "A very nice Item"},
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }