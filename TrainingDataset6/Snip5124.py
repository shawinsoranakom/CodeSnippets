def test_read_items(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "name": "Portal Gun",
            "description": None,
            "price": 42.0,
            "tags": [],
            "tax": None,
        },
        {
            "name": "Plumbus",
            "description": None,
            "price": 32.0,
            "tags": [],
            "tax": None,
        },
    ]