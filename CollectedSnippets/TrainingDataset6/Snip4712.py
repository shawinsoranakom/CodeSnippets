def get_module(request: pytest.FixtureRequest):
    module = importlib.import_module(f"docs_src.encoder.{request.param}")
    return module