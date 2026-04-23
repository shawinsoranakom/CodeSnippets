async def test_sensors_kt100(hass: HomeAssistant) -> None:
    """Test setting up creates the sensors for Kegtron KT-100."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="D0:CF:5E:5C:9B:75",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0

    inject_bluetooth_service_info(
        hass,
        KEGTRON_KT100_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 7

    port_count_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_count")
    port_count_sensor_attrs = port_count_sensor.attributes
    assert port_count_sensor.state == "Single port device"
    assert (
        port_count_sensor_attrs[ATTR_FRIENDLY_NAME] == "Kegtron KT-100 9B75 Port Count"
    )

    keg_size_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_keg_size")
    keg_size_sensor_attrs = keg_size_sensor.attributes
    assert keg_size_sensor.state == "18.927"
    assert keg_size_sensor_attrs[ATTR_FRIENDLY_NAME] == "Kegtron KT-100 9B75 Keg Size"
    assert keg_size_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "L"

    keg_type_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_keg_type")
    keg_type_sensor_attrs = keg_type_sensor.attributes
    assert keg_type_sensor.state == "Corny (5.0 gal)"
    assert keg_type_sensor_attrs[ATTR_FRIENDLY_NAME] == "Kegtron KT-100 9B75 Keg Type"

    volume_start_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_volume_start")
    volume_start_sensor_attrs = volume_start_sensor.attributes
    assert volume_start_sensor.state == "5.0"
    assert (
        volume_start_sensor_attrs[ATTR_FRIENDLY_NAME]
        == "Kegtron KT-100 9B75 Volume Start"
    )
    assert volume_start_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "L"

    volume_dispensed_sensor = hass.states.get(
        "sensor.kegtron_kt_100_9b75_volume_dispensed"
    )
    volume_dispensed_attrs = volume_dispensed_sensor.attributes
    assert volume_dispensed_sensor.state == "0.738"
    assert (
        volume_dispensed_attrs[ATTR_FRIENDLY_NAME]
        == "Kegtron KT-100 9B75 Volume Dispensed"
    )
    assert volume_dispensed_attrs[ATTR_UNIT_OF_MEASUREMENT] == "L"
    assert volume_dispensed_attrs[ATTR_STATE_CLASS] == "total"

    port_state_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_state")
    port_state_sensor_attrs = port_state_sensor.attributes
    assert port_state_sensor.state == "Configured"
    assert (
        port_state_sensor_attrs[ATTR_FRIENDLY_NAME] == "Kegtron KT-100 9B75 Port State"
    )

    port_name_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_name")
    port_name_attrs = port_name_sensor.attributes
    assert port_name_sensor.state == "Single Port"
    assert port_name_attrs[ATTR_FRIENDLY_NAME] == "Kegtron KT-100 9B75 Port Name"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()