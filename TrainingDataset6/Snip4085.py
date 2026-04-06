def test_security_http_digest_incorrect_scheme_credentials():
    response = client.get(
        "/users/me", headers={"Authorization": "Other invalidauthorization"}
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["WWW-Authenticate"] == "Digest"