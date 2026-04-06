def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.dataclasses_.{request.param}")

    client = TestClient(mod.app)
    client.headers.clear()
    return client