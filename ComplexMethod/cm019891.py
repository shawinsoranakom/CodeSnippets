async def test_sensors_aranet_radiation(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test setting up creates the sensors for Aranet Radiation device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 0
    inject_bluetooth_service_info(hass, VALID_ARANET_RADIATION_DATA_SERVICE_INFO)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 4

    batt_sensor = hass.states.get("sensor.aranet_12345_battery")
    batt_sensor_attrs = batt_sensor.attributes
    assert batt_sensor.state == "100"
    assert batt_sensor_attrs[ATTR_FRIENDLY_NAME] == "Aranet\u2622 12345 Battery"
    assert batt_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert batt_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    humid_sensor = hass.states.get("sensor.aranet_12345_radiation_total_dose")
    humid_sensor_attrs = humid_sensor.attributes
    assert humid_sensor.state == "0.011616"
    assert (
        humid_sensor_attrs[ATTR_FRIENDLY_NAME]
        == "Aranet\u2622 12345 Radiation Total Dose"
    )
    assert humid_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "mSv"
    assert humid_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    temp_sensor = hass.states.get("sensor.aranet_12345_radiation_dose_rate")
    temp_sensor_attrs = temp_sensor.attributes
    assert temp_sensor.state == "0.11"
    assert (
        temp_sensor_attrs[ATTR_FRIENDLY_NAME]
        == "Aranet\u2622 12345 Radiation Dose Rate"
    )
    assert temp_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "μSv/h"
    assert temp_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    interval_sensor = hass.states.get("sensor.aranet_12345_update_interval")
    interval_sensor_attrs = interval_sensor.attributes
    assert interval_sensor.state == "300"
    assert (
        interval_sensor_attrs[ATTR_FRIENDLY_NAME]
        == "Aranet\u2622 12345 Update Interval"
    )
    assert interval_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT] == "s"
    assert interval_sensor_attrs[ATTR_STATE_CLASS] == "measurement"

    # Check device context for the battery sensor
    entity = entity_registry.async_get("sensor.aranet_12345_battery")
    device = device_registry.async_get(entity.device_id)
    assert device.name == "Aranet☢ 12345"
    assert device.model == "Aranet Radiation"
    assert device.sw_version == "v1.4.38"
    assert device.manufacturer == "SAF Tehnika"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()