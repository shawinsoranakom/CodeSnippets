def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.security.{request.param}")
    return TestClient(mod.app)