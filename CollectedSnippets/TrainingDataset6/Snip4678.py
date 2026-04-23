def get_module(request: pytest.FixtureRequest):
    mod_name = f"docs_src.dependencies.{request.param}"
    mod = importlib.import_module(mod_name)
    return mod