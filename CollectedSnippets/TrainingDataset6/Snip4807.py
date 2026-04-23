def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.header_params.{request.param}")

    client = TestClient(mod.app)
    return client