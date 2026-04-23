async def test_unavailable(hass: HomeAssistant) -> None:
    """Test normal device goes to unavailable after 60 minutes."""
    start_monotonic = time.monotonic()

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:66:E5:67",
        data={"bindkey": "0fdcc30fe9289254876b5ef7c11ef1f0"},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "A4:C1:38:66:E5:67",
            b"XY\x89\x18\x9ag\xe5f8\xc1\xa4\x9d\xd9z\xf3&\x00\x00\xc8\xa6\x0b\xd5",
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

    # Normal devices should go to unavailable
    assert opening_sensor.state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert CONF_SLEEPY_DEVICE not in entry.data