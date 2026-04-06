def test_security_http_base_with_whitespaces():
    response = client.get("/users/me", headers={"Authorization": "Other  foobar "})
    assert response.status_code == 200, response.text
    assert response.json() == {"scheme": "Other", "credentials": "foobar"}