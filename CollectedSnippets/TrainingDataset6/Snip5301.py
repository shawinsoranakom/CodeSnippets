def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.stream_data.{request.param}")

    client = TestClient(mod.app)
    return client