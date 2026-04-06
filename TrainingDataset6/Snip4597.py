def test(path, cookies, expected_status, expected_response, mod: ModuleType):
    client = TestClient(mod.app, cookies=cookies)
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.json() == expected_response