def test_token(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "username": "testtokenfakedecoded",
        "email": "john@example.com",
        "full_name": "John Doe",
        "disabled": None,
    }