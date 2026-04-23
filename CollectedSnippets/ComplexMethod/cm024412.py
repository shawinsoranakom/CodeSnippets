async def test_device_tracker_random_address(hass: HomeAssistant) -> None:
    """Test creating and updating device_tracker."""
    entry = MockConfigEntry(
        domain=DOMAIN,
    )
    entry.add_to_hass(hass)
    start_time = time.monotonic()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    for i in range(20):
        inject_bluetooth_service_info(
            hass,
            replace(
                BEACON_RANDOM_ADDRESS_SERVICE_INFO, address=f"AA:BB:CC:DD:EE:{i:02X}"
            ),
        )
    await hass.async_block_till_done()

    tracker = hass.states.get("device_tracker.randomaddress_1234")
    tracker_attributes = tracker.attributes
    assert tracker.state == STATE_HOME
    assert tracker_attributes[ATTR_FRIENDLY_NAME] == "RandomAddress_1234"

    await hass.async_block_till_done()
    with (
        patch_all_discovered_devices([]),
        patch(
            "homeassistant.components.ibeacon.coordinator.MONOTONIC_TIME",
            return_value=start_time + UNAVAILABLE_TIMEOUT + 1,
        ),
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TIMEOUT)
        )
        await hass.async_block_till_done()

    tracker = hass.states.get("device_tracker.randomaddress_1234")
    assert tracker.state == STATE_NOT_HOME

    inject_bluetooth_service_info(
        hass, replace(BEACON_RANDOM_ADDRESS_SERVICE_INFO, address="AA:BB:CC:DD:EE:DD")
    )
    await hass.async_block_till_done()

    tracker = hass.states.get("device_tracker.randomaddress_1234")
    tracker_attributes = tracker.attributes
    assert tracker.state == STATE_HOME
    assert tracker_attributes[ATTR_FRIENDLY_NAME] == "RandomAddress_1234"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    tracker = hass.states.get("device_tracker.randomaddress_1234")
    tracker_attributes = tracker.attributes
    assert tracker.state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    tracker = hass.states.get("device_tracker.randomaddress_1234")
    tracker_attributes = tracker.attributes
    assert tracker.state == STATE_HOME
    assert tracker_attributes[ATTR_FRIENDLY_NAME] == "RandomAddress_1234"