def test_get_root():
    response = client.get("/", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello, World!"}