def test_post_with_only_name(client: TestClient):
    response = client.post("/items/", json={"name": "Foo"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "price"],
                "msg": "Field required",
                "input": {"name": "Foo"},
            }
        ]
    }