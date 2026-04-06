def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.extra_models.{request.param}")

    client = TestClient(mod.app)
    return client