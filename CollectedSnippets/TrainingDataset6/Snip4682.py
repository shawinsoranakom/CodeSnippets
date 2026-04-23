def test_get_no_item(client: TestClient):
    response = client.get("/items/foo")
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Item not found"}