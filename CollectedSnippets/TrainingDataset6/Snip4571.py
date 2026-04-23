def test_patch_all(client: TestClient):
    response = client.patch(
        "/items/foo",
        json={
            "name": "Fooz",
            "description": "Item description",
            "price": 3,
            "tax": 10.5,
            "tags": ["tag1", "tag2"],
        },
    )
    assert response.json() == {
        "name": "Fooz",
        "description": "Item description",
        "price": 3,
        "tax": 10.5,
        "tags": ["tag1", "tag2"],
    }