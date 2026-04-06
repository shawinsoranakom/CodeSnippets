def get_mod(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.cookie_params.{request.param}")

    return mod