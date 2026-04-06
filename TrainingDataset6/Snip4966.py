def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.query_params.{request.param}")

    c = TestClient(mod.app)
    return c