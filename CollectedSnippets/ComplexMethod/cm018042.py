async def test_platform_specific_config_validation(hass: HomeAssistant) -> None:
    """Test platform that specifies config."""
    platform_schema = cv.PLATFORM_SCHEMA.extend(
        {"valid": True}, extra=vol.PREVENT_EXTRA
    )

    mock_setup = Mock(spec_set=True)

    mock_platform(
        hass,
        "platform_a.switch",
        MockPlatform(platform_schema=platform_schema, setup_platform=mock_setup),
    )

    with (
        assert_setup_component(0, "switch"),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        assert await setup.async_setup_component(
            hass,
            "switch",
            {"switch": {"platform": "platform_a", "invalid": True}},
        )
        await hass.async_block_till_done()
        assert mock_setup.call_count == 0
        assert len(mock_notify.mock_calls) == 1

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("switch")

    with (
        assert_setup_component(0),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        assert await setup.async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "platform_a",
                    "valid": True,
                    "invalid_extra": True,
                }
            },
        )
        await hass.async_block_till_done()
        assert mock_setup.call_count == 0
        assert len(mock_notify.mock_calls) == 1

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("switch")

    with (
        assert_setup_component(1, "switch"),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        assert await setup.async_setup_component(
            hass,
            "switch",
            {"switch": {"platform": "platform_a", "valid": True}},
        )
        await hass.async_block_till_done()
        assert mock_setup.call_count == 1
        assert len(mock_notify.mock_calls) == 0