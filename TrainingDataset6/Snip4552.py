def test_put_empty_body(client: TestClient):
    response = client.post(
        "/offers/",
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
            {
                "loc": ["body", "items"],
                "input": {},
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }