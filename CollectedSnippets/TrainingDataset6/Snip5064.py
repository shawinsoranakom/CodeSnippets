def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.request_files.{request.param}")

    client = TestClient(mod.app)
    return client