def test_bootstrap_error() -> None:
    """Test a valid platform setup."""
    res = check_config.check(get_test_config_dir(YAML_CONFIG_FILE))
    err = res["except"].pop(check_config.ERROR_STR)
    assert len(err) == 1
    assert res["except"] == {}
    assert res["components"] == {}  # No components, load failed
    assert res["secret_cache"] == {}
    assert res["secrets"] == {}
    assert res["warn"] == {}
    assert res["yaml_files"] == {}