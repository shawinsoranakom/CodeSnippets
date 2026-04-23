async def test_platform_not_ready(hass: HomeAssistant) -> None:
    """Test that we retry when platform not ready."""
    platform1_setup = Mock(side_effect=[PlatformNotReady, PlatformNotReady, None])
    mock_integration(hass, MockModule("mod1"))
    mock_platform(
        hass, "mod1.test_domain", MockPlatform(setup_platform=platform1_setup)
    )

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    utcnow = dt_util.utcnow()

    with freeze_time(utcnow):
        await component.async_setup({DOMAIN: {"platform": "mod1"}})
        await hass.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 1
        assert "mod1.test_domain" not in hass.config.components

        # Should not trigger attempt 2
        async_fire_time_changed(hass, utcnow + timedelta(seconds=29))
        await hass.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 1

        # Should trigger attempt 2
        async_fire_time_changed(hass, utcnow + timedelta(seconds=30))
        await hass.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 2
        assert "mod1.test_domain" not in hass.config.components

        # This should not trigger attempt 3
        async_fire_time_changed(hass, utcnow + timedelta(seconds=59))
        await hass.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 2

        # Trigger attempt 3, which succeeds
        async_fire_time_changed(hass, utcnow + timedelta(seconds=60))
        await hass.async_block_till_done()
        assert len(platform1_setup.mock_calls) == 3
        assert "mod1.test_domain" in hass.config.components