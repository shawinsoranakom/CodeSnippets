def test_get_item(client: TestClient):
    response = client.get("/items/portal-gun")
    assert response.status_code == 200, response.text
    assert response.json() == {"description": "Gun to create portals", "owner": "Rick"}