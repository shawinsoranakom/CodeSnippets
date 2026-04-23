def test_package_invalid() -> None:
    """Test an invalid package."""
    res = check_config.check(get_test_config_dir())

    assert res["except"] == {}
    assert res["components"].keys() == {"homeassistant"}
    assert res["secret_cache"] == {}
    assert res["secrets"] == {}
    assert res["warn"].keys() == {"homeassistant.packages.p1.group"}
    assert res["warn"]["homeassistant.packages.p1.group"][1] == {"group": ["a"]}
    assert len(res["yaml_files"]) == 1