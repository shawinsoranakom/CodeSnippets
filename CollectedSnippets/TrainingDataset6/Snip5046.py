def test_get_random_item(client: TestClient):
    response = client.get("/items")
    assert response.status_code == 200, response.text
    assert response.json() == {"id": IsStr(), "name": IsStr()}