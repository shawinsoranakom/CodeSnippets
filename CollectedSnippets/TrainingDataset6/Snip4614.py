def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.custom_request_and_route.{request.param}")

    client = TestClient(mod.app)
    return client