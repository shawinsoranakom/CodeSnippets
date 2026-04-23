def test_patch_name(client: TestClient):
    response = client.patch(
        "/items/bar",
        json={"name": "Barz"},
    )
    assert response.json() == {
        "name": "Barz",
        "description": "The bartenders",
        "price": 62,
        "tax": 20.2,
        "tags": [],
    }