async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_bridge_v2: Mock,
    v2_resources_test_data: JsonArrayType,
) -> None:
    """Test if all v2 sensors get created with correct features."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.SENSOR)
    # there shouldn't have been any requests at this point
    assert len(mock_bridge_v2.mock_requests) == 0
    # 7 entities should be created from test data
    assert len(hass.states.async_all()) == 7

    # test temperature sensor
    sensor = hass.states.get("sensor.hue_motion_sensor_temperature")
    assert sensor is not None
    assert sensor.state == "18.1"
    assert sensor.attributes["friendly_name"] == "Hue motion sensor Temperature"
    assert sensor.attributes["device_class"] == "temperature"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "°C"

    # test illuminance sensor
    sensor = hass.states.get("sensor.hue_motion_sensor_illuminance")
    assert sensor is not None
    assert sensor.state == "63"
    assert sensor.attributes["friendly_name"] == "Hue motion sensor Illuminance"
    assert sensor.attributes["device_class"] == "illuminance"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "lx"
    assert sensor.attributes["light_level"] == 18027

    # test battery sensor
    sensor = hass.states.get("sensor.wall_switch_with_2_controls_battery")
    assert sensor is not None
    assert sensor.state == "100"
    assert sensor.attributes["friendly_name"] == "Wall switch with 2 controls Battery"
    assert sensor.attributes["device_class"] == "battery"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "%"
    assert sensor.attributes["battery_state"] == "normal"

    # test grouped light level sensor
    sensor = hass.states.get("sensor.sensor_group_illuminance")
    assert sensor is not None
    assert sensor.state == "0"
    assert sensor.attributes["friendly_name"] == "Sensor group Illuminance"
    assert sensor.attributes["device_class"] == "illuminance"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "lx"
    assert sensor.attributes["light_level"] == 0

    # test disabled zigbee_connectivity sensor
    entity_id = "sensor.wall_switch_with_2_controls_zigbee_connectivity"
    entity_entry = entity_registry.async_get(entity_id)

    assert entity_entry
    assert entity_entry.disabled
    assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION