def test_get_item_does_not_exist(client: TestClient):
    response = client.get("/items?id=isbn-nope")
    assert response.status_code == 200, response.text
    assert response.json() == {"id": "isbn-nope", "name": None}