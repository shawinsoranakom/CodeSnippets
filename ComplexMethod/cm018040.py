async def test_validate_platform_config(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test validating platform configuration."""
    platform_schema = cv.PLATFORM_SCHEMA.extend({"hello": str})
    platform_schema_base = cv.PLATFORM_SCHEMA_BASE.extend({})
    mock_integration(
        hass,
        MockModule("platform_conf", platform_schema_base=platform_schema_base),
    )
    mock_platform(
        hass,
        "whatever.platform_conf",
        MockPlatform(platform_schema=platform_schema),
    )

    with assert_setup_component(0):
        assert await setup.async_setup_component(
            hass,
            "platform_conf",
            {"platform_conf": {"platform": "not_existing", "hello": "world"}},
        )

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    with assert_setup_component(1):
        assert await setup.async_setup_component(
            hass,
            "platform_conf",
            {"platform_conf": {"platform": "whatever", "hello": "world"}},
        )

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    with assert_setup_component(1):
        assert await setup.async_setup_component(
            hass,
            "platform_conf",
            {"platform_conf": [{"platform": "whatever", "hello": "world"}]},
        )

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    # Any falsey platform config will be ignored (None, {}, etc)
    with assert_setup_component(0) as config:
        assert await setup.async_setup_component(
            hass, "platform_conf", {"platform_conf": None}
        )
        assert "platform_conf" in hass.config.components
        assert not config["platform_conf"]  # empty

        assert await setup.async_setup_component(
            hass, "platform_conf", {"platform_conf": {}}
        )
        assert "platform_conf" in hass.config.components
        assert not config["platform_conf"]