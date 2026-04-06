def test_put_empty_body(client: TestClient):
    response = client.put(
        "/items/5",
        json={},
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "name"],
                "input": {},
                "msg": "Field required",
                "type": "missing",
            },
            {
                "loc": ["body", "price"],
                "input": {},
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }