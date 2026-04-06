def test_post_item(client: TestClient):
    response = client.post("/items/", json={"name": "Foo", "price": 3})
    assert response.status_code == 200
    assert response.json() == {
        "name": "Foo",
        "price": 3,
        "description": None,
        "tax": None,
    }