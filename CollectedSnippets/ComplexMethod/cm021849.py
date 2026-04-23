async def test_hmip_acceleration_sensor(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipAccelerationSensor."""
    entity_id = "binary_sensor.garagentor"
    entity_name = "Garagentor"
    device_model = "HmIP-SAM"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert ha_state.attributes[ATTR_ACCELERATION_SENSOR_MODE] == "FLAT_DECT"
    assert ha_state.attributes[ATTR_ACCELERATION_SENSOR_NEUTRAL_POSITION] == "VERTICAL"
    assert (
        ha_state.attributes[ATTR_ACCELERATION_SENSOR_SENSITIVITY] == "SENSOR_RANGE_4G"
    )
    assert ha_state.attributes[ATTR_ACCELERATION_SENSOR_TRIGGER_ANGLE] == 45
    service_call_counter = len(hmip_device.mock_calls)

    await async_manipulate_test_data(
        hass, hmip_device, "accelerationSensorTriggered", False
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF
    assert len(hmip_device.mock_calls) == service_call_counter + 1

    await async_manipulate_test_data(
        hass, hmip_device, "accelerationSensorTriggered", True
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON
    assert len(hmip_device.mock_calls) == service_call_counter + 2