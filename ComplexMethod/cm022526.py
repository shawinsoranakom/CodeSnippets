async def test_reload_all(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reload_all service."""
    await async_setup_component(hass, "homeassistant", {})
    test1 = async_mock_service(hass, "test1", "reload")
    test2 = async_mock_service(hass, "test2", "reload")
    no_reload = async_mock_service(hass, "test3", "not_reload")
    notify = async_mock_service(hass, "notify", "reload")
    core_config = async_mock_service(hass, "homeassistant", "reload_core_config")
    themes = async_mock_service(hass, "frontend", "reload_themes")
    jinja = async_mock_service(hass, "homeassistant", "reload_custom_templates")

    with patch(
        "homeassistant.config.async_check_ha_config_file",
        return_value=None,
    ) as mock_async_check_ha_config_file:
        await hass.services.async_call(
            "homeassistant",
            SERVICE_RELOAD_ALL,
            blocking=True,
        )

    assert mock_async_check_ha_config_file.called
    assert len(test1) == 1
    assert len(test2) == 1
    assert len(no_reload) == 0
    assert len(notify) == 0
    assert len(core_config) == 1
    assert len(themes) == 1

    with (
        pytest.raises(
            HomeAssistantError,
            match=(
                "Cannot quick reload all YAML configurations because the configuration is "
                "not valid: Oh no, drama!"
            ),
        ),
        patch(
            "homeassistant.config.async_check_ha_config_file",
            return_value="Oh no, drama!",
        ) as mock_async_check_ha_config_file,
    ):
        await hass.services.async_call(
            "homeassistant",
            SERVICE_RELOAD_ALL,
            blocking=True,
        )

    assert mock_async_check_ha_config_file.called
    assert (
        "The system cannot reload because the configuration is not valid: Oh no, drama!"
        in caplog.text
    )

    # None have been called again
    assert len(test1) == 1
    assert len(test2) == 1
    assert len(core_config) == 1
    assert len(themes) == 1
    assert len(jinja) == 1