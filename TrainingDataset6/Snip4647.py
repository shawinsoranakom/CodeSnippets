def test_post_invalid_item(client: TestClient):
    response = client.post("/items/", json={"name": "Foo", "price": "invalid price"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "float_parsing",
                "loc": ["body", "price"],
                "msg": "Input should be a valid number, unable to parse string as a number",
                "input": "invalid price",
            }
        ]
    }