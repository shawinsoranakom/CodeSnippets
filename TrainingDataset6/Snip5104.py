def get_app(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.request_forms_and_files.{request.param}")

    return mod.app