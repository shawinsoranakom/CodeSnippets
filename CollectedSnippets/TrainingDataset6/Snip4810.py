def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.json_base64_bytes.{request.param}")

    client = TestClient(mod.app)
    return client