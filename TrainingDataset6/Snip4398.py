def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.additional_status_codes.{request.param}")

    client = TestClient(mod.app)
    return client