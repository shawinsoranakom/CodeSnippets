def test_foo_no_needy(client: TestClient):
    response = client.get("/items/foo?skip=a&limit=b")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "needy"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "int_parsing",
                "loc": ["query", "skip"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "a",
            },
            {
                "type": "int_parsing",
                "loc": ["query", "limit"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "b",
            },
        ]
    }