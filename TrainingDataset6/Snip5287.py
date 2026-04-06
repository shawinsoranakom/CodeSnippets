def get_app(request: pytest.FixtureRequest, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    mod = importlib.import_module(f"docs_src.settings.{request.param}")
    return mod.app