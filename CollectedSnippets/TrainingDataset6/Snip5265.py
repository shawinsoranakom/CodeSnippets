def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.server_sent_events.{request.param}")
    client = TestClient(mod.app)
    return client