async def test_sleepy_device_restore_state(hass: HomeAssistant) -> None:
    """Test sleepy devices stay available."""
    start_monotonic = time.monotonic()

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="50:FB:19:1B:B5:DC",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0
    inject_bluetooth_service_info_bleak(hass, MISCALE_V1_SERVICE_INFO)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 2

    mass_non_stabilized_sensor = hass.states.get(
        "sensor.mi_smart_scale_b5dc_weight_non_stabilized"
    )
    assert mass_non_stabilized_sensor.state == "86.55"

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

    mass_non_stabilized_sensor = hass.states.get(
        "sensor.mi_smart_scale_b5dc_weight_non_stabilized"
    )

    # Sleepy devices should keep their state over time
    assert mass_non_stabilized_sensor.state == "86.55"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    mass_non_stabilized_sensor = hass.states.get(
        "sensor.mi_smart_scale_b5dc_weight_non_stabilized"
    )

    # Sleepy devices should keep their state over time and restore it
    assert mass_non_stabilized_sensor.state == "86.55"

    assert entry.data[CONF_SLEEPY_DEVICE] is True