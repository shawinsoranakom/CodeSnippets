async def test_sensors(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors."""
    start_monotonic = time.monotonic()
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ORALB_SERVICE_INFO.address,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, ORALB_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 9

    toothbrush_sensor = hass.states.get("sensor.triumph_d36_48be")
    toothbrush_sensor_attrs = toothbrush_sensor.attributes
    assert toothbrush_sensor.state == "running"
    assert toothbrush_sensor_attrs[ATTR_FRIENDLY_NAME] == "Triumph D36 48BE"
    assert ATTR_ASSUMED_STATE not in toothbrush_sensor_attrs

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    # Fastforward time without BLE advertisements
    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1

    with (
        patch_bluetooth_time(
            monotonic_now,
        ),
        patch_all_discovered_devices([]),
    ):
        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + timedelta(seconds=FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1),
        )
        await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # All of these devices are sleepy so we should still be available
    toothbrush_sensor = hass.states.get("sensor.triumph_d36_48be")
    assert toothbrush_sensor.state == "running"