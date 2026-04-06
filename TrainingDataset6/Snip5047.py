def test_get_item(client: TestClient):
    response = client.get("/items?id=isbn-9781529046137")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": "isbn-9781529046137",
        "name": "The Hitchhiker's Guide to the Galaxy",
    }