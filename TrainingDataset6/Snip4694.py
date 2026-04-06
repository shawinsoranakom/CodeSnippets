def test_internal_server_error(mod: ModuleType):
    client = TestClient(mod.app, raise_server_exceptions=False)
    response = client.get("/items/portal-gun")
    assert response.status_code == 500, response.text
    assert response.text == "Internal Server Error"