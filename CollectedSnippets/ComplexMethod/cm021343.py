async def test_sensors_io_series_4(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors with an io series 4."""
    start_monotonic = time.monotonic()

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ORALB_IO_SERIES_4_SERVICE_INFO.address,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, ORALB_IO_SERIES_4_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 9

    toothbrush_sensor = hass.states.get("sensor.io_series_4_48be_brushing_mode")
    toothbrush_sensor_attrs = toothbrush_sensor.attributes
    assert toothbrush_sensor.state == "gum_care"
    assert (
        toothbrush_sensor_attrs[ATTR_FRIENDLY_NAME] == "IO Series 4 48BE Brushing mode"
    )
    assert ATTR_ASSUMED_STATE not in toothbrush_sensor_attrs

    # Fast-forward time without BLE advertisements
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
        assert (
            async_address_present(hass, ORALB_IO_SERIES_4_SERVICE_INFO.address) is False
        )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    toothbrush_sensor = hass.states.get("sensor.io_series_4_48be_brushing_mode")
    # Sleepy devices should keep their state over time
    assert toothbrush_sensor.state == "gum_care"
    toothbrush_sensor_attrs = toothbrush_sensor.attributes
    assert toothbrush_sensor_attrs[ATTR_ASSUMED_STATE] is True

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()