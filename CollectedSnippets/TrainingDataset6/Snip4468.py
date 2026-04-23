def test_post_without_tax(client: TestClient, price: str | float):
    response = client.post(
        "/items/", json={"name": "Foo", "price": price, "description": "Some Foo"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "Foo",
        "price": 50.5,
        "description": "Some Foo",
        "tax": None,
    }