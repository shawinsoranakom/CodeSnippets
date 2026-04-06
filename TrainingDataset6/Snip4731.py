def test_post(client: TestClient):
    response = client.post(
        "/user/",
        json={
            "username": "johndoe",
            "password": "secret",
            "email": "johndoe@example.com",
            "full_name": "John Doe",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "username": "johndoe",
        "email": "johndoe@example.com",
        "full_name": "John Doe",
    }