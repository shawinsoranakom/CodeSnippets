def get_mod(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.security.{request.param}")

    return mod