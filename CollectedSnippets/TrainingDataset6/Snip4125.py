def test_root():
    response = client.get("/", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello World"}