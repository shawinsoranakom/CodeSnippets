def get_mod(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.websockets_.{request.param}")

    return mod