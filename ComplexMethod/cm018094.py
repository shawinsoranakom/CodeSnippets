def test_secrets() -> None:
    """Test secrets config checking method."""
    res = check_config.check(get_test_config_dir(), True)

    assert res["except"] == {}
    assert res["components"].keys() == {"homeassistant", "http"}
    assert res["components"]["http"] == {
        "cors_allowed_origins": ["http://google.com"],
        "ip_ban_enabled": True,
        "login_attempts_threshold": -1,
        "server_port": 8123,
        "ssl_profile": "modern",
        "use_x_frame_options": True,
    }
    assert res["secret_cache"] == {
        get_test_config_dir("secrets.yaml"): {"http_pw": "http://google.com"}
    }
    assert res["secrets"] == {"http_pw": "http://google.com"}
    assert res["warn"] == {}
    assert normalize_yaml_files(res) == [
        ".../configuration.yaml",
        ".../secrets.yaml",
    ]