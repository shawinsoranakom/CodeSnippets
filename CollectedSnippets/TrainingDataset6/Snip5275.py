def test_settings_validation_error(mod_name: str, monkeypatch: MonkeyPatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    if mod_name in sys.modules:
        del sys.modules[mod_name]  # pragma: no cover

    with pytest.raises(ValidationError) as exc_info:
        importlib.import_module(mod_name)
    assert exc_info.value.errors() == [
        {
            "loc": ("admin_email",),
            "msg": "Field required",
            "type": "missing",
            "input": {},
            "url": IsAnyStr,
        }
    ]