def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(
        f"docs_src.authentication_error_status_code.{request.param}"
    )

    client = TestClient(mod.app)
    return client