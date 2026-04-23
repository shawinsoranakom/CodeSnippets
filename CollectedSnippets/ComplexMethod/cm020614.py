async def test_sleepy_device(hass: HomeAssistant) -> None:
    """Test sleepy device does not go to unavailable after 60 minutes."""
    start_monotonic = time.monotonic()

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:66:E5:67",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "A4:C1:38:66:E5:67",
            b"@0\xd6\x03$\x19\x10\x01\x00",
        ),
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 1

    opening_sensor = hass.states.get("binary_sensor.door_window_sensor_e567_opening")

    assert opening_sensor.state == STATE_ON

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

    opening_sensor = hass.states.get("binary_sensor.door_window_sensor_e567_opening")

    # Sleepy devices should keep their state over time
    assert opening_sensor.state == STATE_ON

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.data[CONF_SLEEPY_DEVICE] is True