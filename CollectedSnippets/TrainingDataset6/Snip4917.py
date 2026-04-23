def get_client(request: pytest.FixtureRequest) -> TestClient:
    mod = importlib.import_module(
        f"docs_src.path_params_numeric_validations.{request.param}"
    )
    return TestClient(mod.app)