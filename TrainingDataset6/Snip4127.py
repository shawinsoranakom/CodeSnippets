def test_read_with_get_token():
    response = client.get(
        "/with-get-token", headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Admin Access"}