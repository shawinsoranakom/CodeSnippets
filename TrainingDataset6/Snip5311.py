def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.strict_content_type.{request.param}")
    client = TestClient(mod.app)
    return client