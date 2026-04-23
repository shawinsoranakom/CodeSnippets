def get_client(request: pytest.FixtureRequest) -> TestClient:
    mod = importlib.import_module(f"docs_src.separate_openapi_schemas.{request.param}")

    client = TestClient(mod.app)
    return client