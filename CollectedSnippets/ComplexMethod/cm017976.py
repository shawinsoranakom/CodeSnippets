async def test_create_default_config(hass: HomeAssistant) -> None:
    """Test creation of default config."""
    assert not os.path.isfile(YAML_PATH)
    assert not os.path.isfile(SECRET_PATH)
    assert not os.path.isfile(VERSION_PATH)
    assert not os.path.isfile(AUTOMATIONS_PATH)

    await config_util.async_create_default_config(hass)

    assert os.path.isfile(YAML_PATH)
    assert os.path.isfile(SECRET_PATH)
    assert os.path.isfile(VERSION_PATH)
    assert os.path.isfile(AUTOMATIONS_PATH)