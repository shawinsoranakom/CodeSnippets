def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.extra_data_types.{request.param}")

    client = TestClient(mod.app)
    return client