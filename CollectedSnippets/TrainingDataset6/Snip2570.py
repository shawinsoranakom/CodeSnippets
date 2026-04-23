def test_app_level_dep_scope_function() -> None:
    app = FastAPI(dependencies=[Depends(raise_after_yield, scope="function")])

    @app.get("/app-scope-function")
    def get_app_scope_function():
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/app-scope-function")
        assert response.status_code == 503
        assert response.json() == {"detail": "Exception after yield"}