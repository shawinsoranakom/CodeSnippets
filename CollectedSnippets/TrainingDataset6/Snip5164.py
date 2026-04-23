def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.schema_extra_example.{request.param}")

    client = TestClient(mod.app)
    return client