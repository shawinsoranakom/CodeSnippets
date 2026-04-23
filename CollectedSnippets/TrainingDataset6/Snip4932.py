def get_module(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.python_types.{request.param}")
    return mod