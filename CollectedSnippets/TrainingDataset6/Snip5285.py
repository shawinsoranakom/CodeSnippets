def test_settings(main_mod: ModuleType, monkeypatch: MonkeyPatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    settings = main_mod.get_settings()
    assert settings.app_name == "Awesome API"
    assert settings.admin_email == "admin@example.com"
    assert settings.items_per_user == 50