def test_token_with_whitespaces():
    response = client.get("/items", headers={"Authorization": "Bearer  testtoken "})
    assert response.status_code == 200, response.text
    assert response.json() == {"token": "testtoken"}