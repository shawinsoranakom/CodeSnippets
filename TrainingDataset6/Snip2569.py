def test_router_level_dep_scope_request() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/router-scope-request/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}