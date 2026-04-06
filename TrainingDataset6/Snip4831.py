def get_mod(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.openapi_callbacks.{request.param}")
    return mod