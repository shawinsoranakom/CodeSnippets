async def test_sensors_updates_fixed_mac_address(hass: HomeAssistant) -> None:
    """Test creating and updating sensors with a fixed mac address."""
    entry = MockConfigEntry(
        domain=DOMAIN,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch_all_discovered_devices([BLUECHARM_BLE_DEVICE]):
        inject_bluetooth_service_info(hass, BLUECHARM_BEACON_SERVICE_INFO)
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.bluecharm_177999_8105_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "2"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME]
        == "BlueCharm_177999 8105 Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    with patch_all_discovered_devices([BLUECHARM_BLE_DEVICE]):
        inject_bluetooth_service_info(hass, BLUECHARM_BEACON_SERVICE_INFO_2)
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.bluecharm_177999_8105_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "0"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME]
        == "BlueCharm_177999 8105 Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    # Make sure RSSI updates are picked up by the periodic update
    inject_bluetooth_service_info(
        hass, replace(BLUECHARM_BEACON_SERVICE_INFO_2, rssi=-84)
    )

    # We should not see it right away since the update interval is 60 seconds
    distance_sensor = hass.states.get("sensor.bluecharm_177999_8105_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "0"

    with patch_all_discovered_devices([BLUECHARM_BLE_DEVICE]):
        async_fire_time_changed(
            hass,
            dt_util.utcnow() + timedelta(seconds=UPDATE_INTERVAL.total_seconds() * 2),
        )
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.bluecharm_177999_8105_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "14"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME]
        == "BlueCharm_177999 8105 Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    with patch_all_discovered_devices([]):
        await hass.async_block_till_done()
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS * 2)
        )
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.bluecharm_177999_8105_estimated_distance")
    assert distance_sensor.state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()