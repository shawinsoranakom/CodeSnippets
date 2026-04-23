async def test_log_object_sources(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test we can setup and the service and we can dump objects to the log."""

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_START_LOG_OBJECT_SOURCES)
    assert hass.services.has_service(DOMAIN, SERVICE_STOP_LOG_OBJECT_SOURCES)

    class FakeObject:
        """Fake object."""

        def __repr__(self):
            """Return a fake repr.""."""
            return "<FakeObject>"

    fake_object = FakeObject()

    with patch("gc.collect"), patch("gc.get_objects", return_value=[fake_object]):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_START_LOG_OBJECT_SOURCES,
            {CONF_SCAN_INTERVAL: 10},
            blocking=True,
        )
        with pytest.raises(HomeAssistantError, match="Object logging already started"):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_START_LOG_OBJECT_SOURCES,
                {CONF_SCAN_INTERVAL: 10},
                blocking=True,
            )

        assert "New object FakeObject (0/1)" in caplog.text
        caplog.clear()

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert "No new object growth found" in caplog.text

    fake_object2 = FakeObject()

    with (
        patch("gc.collect"),
        patch("gc.get_objects", return_value=[fake_object, fake_object2]),
    ):
        caplog.clear()

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert "New object FakeObject (1/2)" in caplog.text

    many_objects = [FakeObject() for _ in range(30)]
    with patch("gc.collect"), patch("gc.get_objects", return_value=many_objects):
        caplog.clear()

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert "New object FakeObject (2/30)" in caplog.text
        assert "New objects overflowed by {'FakeObject': 25}" in caplog.text

    await hass.services.async_call(
        DOMAIN, SERVICE_STOP_LOG_OBJECT_SOURCES, {}, blocking=True
    )
    caplog.clear()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=41))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "FakeObject" not in caplog.text
    assert "No new object growth found" not in caplog.text

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=51))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert "FakeObject" not in caplog.text
    assert "No new object growth found" not in caplog.text

    with pytest.raises(HomeAssistantError, match="Object logging not running"):
        await hass.services.async_call(
            DOMAIN, SERVICE_STOP_LOG_OBJECT_SOURCES, {}, blocking=True
        )