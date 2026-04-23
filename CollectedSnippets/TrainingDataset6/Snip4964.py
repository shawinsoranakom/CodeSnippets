def test_foo_no_needy():
    response = client.get("/items/foo")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "needy"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }