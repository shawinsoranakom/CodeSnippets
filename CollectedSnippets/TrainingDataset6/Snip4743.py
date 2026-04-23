def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.first_steps.{request.param}")
    client = TestClient(mod.app)
    return client