def test_get(path, cookie, expected_status, expected_response, client: TestClient):
    if cookie is not None:
        client.cookies.set("last_query", cookie)
    else:
        client.cookies.clear()
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.json() == expected_response