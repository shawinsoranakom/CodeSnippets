def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.custom_response.{request.param}")
    client = TestClient(mod.app)
    return client