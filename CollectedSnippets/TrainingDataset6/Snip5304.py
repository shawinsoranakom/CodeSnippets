def get_mod(request: pytest.FixtureRequest):
    return importlib.import_module(f"docs_src.stream_data.{request.param}")