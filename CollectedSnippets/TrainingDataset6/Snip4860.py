def get_client(request: pytest.FixtureRequest) -> TestClient:
    mod = importlib.import_module(
        f"docs_src.path_operation_configuration.{request.param}"
    )
    return TestClient(mod.app)