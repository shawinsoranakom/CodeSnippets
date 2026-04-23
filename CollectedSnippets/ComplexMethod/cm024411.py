async def test_multiple_uuids_same_beacon(hass: HomeAssistant) -> None:
    """Test a beacon that broadcasts multiple uuids."""
    entry = MockConfigEntry(
        domain=DOMAIN,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch_all_discovered_devices([FEASY_BEACON_BLE_DEVICE]):
        inject_bluetooth_service_info(hass, FEASY_BEACON_SERVICE_INFO_1)
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.fsc_bp108_eeff_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "400"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME] == "FSC-BP108 EEFF Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    with patch_all_discovered_devices([FEASY_BEACON_BLE_DEVICE]):
        inject_bluetooth_service_info(hass, FEASY_BEACON_SERVICE_INFO_2)
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.fsc_bp108_eeff_estimated_distance_2")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "0"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME] == "FSC-BP108 EEFF Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    with patch_all_discovered_devices([FEASY_BEACON_BLE_DEVICE]):
        inject_bluetooth_service_info(hass, FEASY_BEACON_SERVICE_INFO_1)
        await hass.async_block_till_done()

    distance_sensor = hass.states.get("sensor.fsc_bp108_eeff_estimated_distance")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "400"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME] == "FSC-BP108 EEFF Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"

    distance_sensor = hass.states.get("sensor.fsc_bp108_eeff_estimated_distance_2")
    distance_attributes = distance_sensor.attributes
    assert distance_sensor.state == "0"
    assert (
        distance_attributes[ATTR_FRIENDLY_NAME] == "FSC-BP108 EEFF Estimated distance"
    )
    assert distance_attributes[ATTR_UNIT_OF_MEASUREMENT] == "m"
    assert distance_attributes[ATTR_STATE_CLASS] == "measurement"