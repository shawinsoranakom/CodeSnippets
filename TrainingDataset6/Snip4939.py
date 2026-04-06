def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.query_param_models.{request.param}")

    client = TestClient(mod.app)
    return client