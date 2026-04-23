async def test_sensors_aranet2(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test setting up creates the sensors for Aranet2 device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, VALID_ARANET2_DATA_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4

    batt_sensor = hass.states.get("sensor.aranet2_12345_battery")
    batt_sensor_attrs = batt_sensor.attributes
    assert batt_sensor.state == "79"
    assert batt_sensor_attrs[ATTR_FRIENDLY_NAME] == "Aranet2 12345 Battery"
    assert batt_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert batt_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    humid_sensor = hass.states.get("sensor.aranet2_12345_humidity")
    humid_sensor_attrs = humid_sensor.attributes
    assert humid_sensor.state == "52.4"
    assert humid_sensor_attrs[ATTR_FRIENDLY_NAME] == "Aranet2 12345 Humidity"
    assert humid_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert humid_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    temp_sensor = hass.states.get("sensor.aranet2_12345_temperature")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "24.8"
    assert temp_sensor_attrs[ATTR_FRIENDLY_NAME] == "Aranet2 12345 Temperature"
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    interval_sensor = hass.states.get("sensor.aranet2_12345_update_interval")
    interval_sensor_attrs = interval_sensor.attributes
    assert interval_sensor.state == "60"
    assert interval_sensor_attrs[ATTR_FRIENDLY_NAME] == "Aranet2 12345 Update Interval"
    assert interval_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "s"
    assert interval_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    # Check device context for the battery sensor
    entity = entity_registry.async_get("sensor.aranet2_12345_battery")
    device = device_registry.async_get(entity.device_id)
    assert device.name == "Aranet2 12345"
    assert device.model == "Aranet2"
    assert device.sw_version == "v1.4.4"
    assert device.manufacturer == "SAF Tehnika"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()