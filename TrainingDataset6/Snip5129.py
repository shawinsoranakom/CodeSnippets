def test_post_user(client: TestClient):
    user_data = {
        "username": "foo",
        "password": "fighter",
        "email": "foo@example.com",
        "full_name": "Grave Dohl",
    }
    response = client.post(
        "/user/",
        json=user_data,
    )
    assert response.status_code == 200, response.text
    assert response.json() == user_data