def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.additional_responses.{request.param}")

    client = TestClient(mod.app)
    client.headers.clear()
    return client