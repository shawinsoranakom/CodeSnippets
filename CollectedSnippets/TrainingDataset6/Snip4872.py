def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(
        f"docs_src.path_operation_configuration.{request.param}"
    )

    client = TestClient(mod.app)
    return client