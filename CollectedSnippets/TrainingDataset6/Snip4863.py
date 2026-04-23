def test_get_users(client: TestClient):
    response = client.get("/users/")
    assert response.status_code == 200, response.text
    assert response.json() == [{"username": "johndoe"}]