def test_put_all(client: TestClient, mod_name: str):
    if mod_name.startswith("tutorial003"):
        tags_expected = IsList("foo", "bar", check_order=False)
    else:
        tags_expected = ["foo", "bar", "foo"]

    response = client.put(
        "/items/123",
        json={
            "name": "Foo",
            "description": "A very nice Item",
            "price": 35.4,
            "tax": 3.2,
            "tags": ["foo", "bar", "foo"],
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
            "tags": tags_expected,
        },
    }