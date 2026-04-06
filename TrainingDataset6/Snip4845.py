def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(
        f"docs_src.path_operation_advanced_configuration.{request.param}"
    )

    client = TestClient(mod.app)
    client.headers.clear()
    return client