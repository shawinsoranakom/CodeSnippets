def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.body_updates.{request.param}")

    client = TestClient(mod.app)
    return client