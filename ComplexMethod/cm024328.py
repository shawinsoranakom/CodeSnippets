async def test_object_growth_logging(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we can setup and the service and we can dump objects to the log."""

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_START_LOG_OBJECTS)
    assert hass.services.has_service(DOMAIN, SERVICE_STOP_LOG_OBJECTS)

    with patch.object(objgraph, "growth"):
        await hass.services.async_call(
            DOMAIN, SERVICE_START_LOG_OBJECTS, {CONF_SCAN_INTERVAL: 1}, blocking=True
        )
        with pytest.raises(HomeAssistantError, match="Object logging already started"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_START_LOG_OBJECTS,
                {CONF_SCAN_INTERVAL: 1},
                blocking=True,
            )

        assert "Growth" in caplog.text
        await hass.async_block_till_done(wait_background_tasks=True)
        caplog.clear()

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert "Growth" in caplog.text

    await hass.services.async_call(DOMAIN, SERVICE_STOP_LOG_OBJECTS, {}, blocking=True)
    caplog.clear()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "Growth" not in caplog.text

    with pytest.raises(HomeAssistantError, match="Object logging not running"):
        await hass.services.async_call(
            DOMAIN, SERVICE_STOP_LOG_OBJECTS, {}, blocking=True
        )

    with patch.object(objgraph, "growth"):
        await hass.services.async_call(
            DOMAIN, SERVICE_START_LOG_OBJECTS, {CONF_SCAN_INTERVAL: 10}, blocking=True
        )
        await hass.async_block_till_done(wait_background_tasks=True)
        caplog.clear()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "Growth" not in caplog.text