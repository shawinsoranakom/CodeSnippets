def test_app_level_dep_scope_request() -> None:
    app = FastAPI(dependencies=[Depends(raise_after_yield, scope="request")])

    @app.get("/app-scope-request")
    def get_app_scope_request():
        return {"status": "ok"}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/app-scope-request")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}