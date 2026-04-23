def get_mod_path(request: pytest.FixtureRequest):
    mod_path = f"docs_src.settings.{request.param}"
    return mod_path