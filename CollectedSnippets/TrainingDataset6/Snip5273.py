def get_mod_name(request: pytest.FixtureRequest):
    return f"docs_src.settings.{request.param}.main"