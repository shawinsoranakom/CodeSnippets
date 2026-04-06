def test_post_with_only_name_price(client: TestClient):
    response = client.post("/items/", json={"name": "Foo", "price": "twenty"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "float_parsing",
                "loc": ["body", "price"],
                "msg": "Input should be a valid number, unable to parse string as a number",
                "input": "twenty",
            }
        ]
    }