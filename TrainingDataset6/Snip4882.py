def test_get_users(user_id: str, expected_response: dict):
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200, response.text
    assert response.json() == expected_response