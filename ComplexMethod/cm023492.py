async def test_unavailable(hass: HomeAssistant) -> None:
    """Test normal device goes to unavailable after 60 minutes."""
    start_monotonic = time.monotonic()

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:8D:18:B2",
        data={},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    inject_bluetooth_service_info(
        hass,
        make_bthome_v2_adv(
            "A4:C1:38:8D:18:B2",
            b"\x40\x04\x13\x8a\x01",
        ),
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1

    pressure_sensor = hass.states.get("sensor.test_device_18b2_pressure")

    assert pressure_sensor.state == "1008.83"

    # Fastforward time without BLE advertisements
    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1

    with patch_bluetooth_time(monotonic_now), patch_all_discovered_devices([]):
        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + timedelta(seconds=FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1),
        )
        await hass.async_block_till_done()

    pressure_sensor = hass.states.get("sensor.test_device_18b2_pressure")

    # Normal devices should go to unavailable
    assert pressure_sensor.state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert CONF_SLEEPY_DEVICE not in entry.data