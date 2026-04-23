async def test_sensors_aranetrn(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test setting up creates the sensors for Aranet Radon device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, VALID_ARANET_RADON_DATA_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 7

    batt_sensor = hass.states.get("sensor.aranetrn_12345_battery")
    batt_sensor_attrs = batt_sensor.attributes
    assert batt_sensor.state == "100"
    assert batt_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Battery"
    assert batt_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert batt_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    co2_sensor = hass.states.get("sensor.aranetrn_12345_radon_concentration")
    co2_sensor_attrs = co2_sensor.attributes
    assert co2_sensor.state == "7"
    assert co2_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Radon Concentration"
    assert co2_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "Bq/m³"
    assert co2_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    humid_sensor = hass.states.get("sensor.aranetrn_12345_humidity")
    humid_sensor_attrs = humid_sensor.attributes
    assert humid_sensor.state == "46.2"
    assert humid_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Humidity"
    assert humid_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert humid_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    temp_sensor = hass.states.get("sensor.aranetrn_12345_temperature")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "25.5"
    assert temp_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Temperature"
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "°C"
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    press_sensor = hass.states.get("sensor.aranetrn_12345_pressure")
    press_sensor_attrs = press_sensor.attributes
    assert press_sensor.state == "1018.5"
    assert press_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Pressure"
    assert press_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "hPa"
    assert press_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    interval_sensor = hass.states.get("sensor.aranetrn_12345_update_interval")
    interval_sensor_attrs = interval_sensor.attributes
    assert interval_sensor.state == "600"
    assert (
        interval_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Update Interval"
    )
    assert interval_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "s"
    assert interval_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    status_sensor = hass.states.get("sensor.aranetrn_12345_threshold")
    status_sensor_attrs = status_sensor.attributes
    assert status_sensor.state == "green"
    assert status_sensor_attrs[ATTR_FRIENDLY_NAME] == "AranetRn+ 12345 Threshold"
    assert status_sensor_attrs[ATTR_OPTIONS] == ["error", "green", "yellow", "red"]

    # Check device context for the battery sensor
    entity = entity_registry.async_get("sensor.aranetrn_12345_battery")
    device = device_registry.async_get(entity.device_id)
    assert device.name == "AranetRn+ 12345"
    assert device.model == "Aranet Radon"
    assert device.sw_version == "v1.6.4"
    assert device.manufacturer == "SAF Tehnika"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()