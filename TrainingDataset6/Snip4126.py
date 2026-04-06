def test_read_with_oauth2_scheme():
    response = client.get(
        "/with-oauth2-scheme", headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Admin Access"}