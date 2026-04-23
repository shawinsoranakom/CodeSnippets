def get_test_client(mod_name: str, monkeypatch: MonkeyPatch) -> TestClient:
    if mod_name in sys.modules:
        del sys.modules[mod_name]  # pragma: no cover
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    main_mod = importlib.import_module(mod_name)
    return TestClient(main_mod.app)