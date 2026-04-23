def test_put_all(client: TestClient):
    response = client.put(
        "/items/123",
        json={
            "name": "Foo",
            "description": "A very nice Item",
            "price": 35.4,
            "tax": 3.2,
            "tags": ["foo", "bar", "foo"],
            "image": {"url": "http://example.com/image.png", "name": "example image"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "item_id": 123,
        "item": {
            "name": "Foo",
            "description": "A very nice Item",
            "price": 35.4,
            "tax": 3.2,
            "tags": IsList("foo", "bar", check_order=False),
            "image": {"url": "http://example.com/image.png", "name": "example image"},
        },
    }