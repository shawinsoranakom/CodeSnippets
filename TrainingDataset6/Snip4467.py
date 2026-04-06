def test_post_with_tax(client: TestClient, price: str | float):
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": price, "description": "Some Foo", "tax": 0.3},
    )
    assert response.status_code == 200
    assert response.json() == {
        "name": "Foo",
        "price": 50.5,
        "description": "Some Foo",
        "tax": 0.3,
        "price_with_tax": 50.8,
    }