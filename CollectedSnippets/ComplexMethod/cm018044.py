async def test_setup_config_entry_from_yaml(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test attempting to setup an integration which only supports config_entries."""
    expected_warning = (
        "The 'test_integration_only_entry' integration does not support YAML setup, "
        "please remove it from your configuration"
    )

    mock_integration(
        hass,
        MockModule(
            "test_integration_only_entry",
            setup=False,
            async_setup_entry=AsyncMock(return_value=True),
        ),
    )

    assert await setup.async_setup_component(hass, "test_integration_only_entry", {})
    assert expected_warning not in caplog.text
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    assert await setup.async_setup_component(
        hass, "test_integration_only_entry", {"test_integration_only_entry": None}
    )
    assert expected_warning in caplog.text
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    assert await setup.async_setup_component(
        hass, "test_integration_only_entry", {"test_integration_only_entry": {}}
    )
    assert expected_warning in caplog.text
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    assert await setup.async_setup_component(
        hass,
        "test_integration_only_entry",
        {"test_integration_only_entry": {"hello": "world"}},
    )
    assert expected_warning in caplog.text
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")