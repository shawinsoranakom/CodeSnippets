def test_config_platform_valid() -> None:
    """Test a valid platform setup."""
    res = check_config.check(get_test_config_dir())
    assert res["components"].keys() == {"homeassistant", "light"}
    assert res["components"]["light"] == [{"platform": "demo"}]
    assert res["except"] == {}
    assert res["secret_cache"] == {}
    assert res["secrets"] == {}
    assert res["warn"] == {}
    assert len(res["yaml_files"]) == 1