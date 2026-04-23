async def test_generic_numeric_sensor_state_class_measurement_angle(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_client: APIClient,
    mock_generic_device_entry: MockGenericDeviceEntryType,
) -> None:
    """Test a generic sensor entity."""
    entity_info = [
        SensorInfo(
            object_id="mysensor",
            key=1,
            name="my sensor",
            state_class=ESPHomeSensorStateClass.MEASUREMENT_ANGLE,
            unit_of_measurement="°",
        )
    ]
    states = [SensorState(key=1, state=50)]
    user_service = []
    await mock_generic_device_entry(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("sensor.test_my_sensor")
    assert state is not None
    assert state.state == "50"
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT_ANGLE
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "°"
    entry = entity_registry.async_get("sensor.test_my_sensor")
    assert entry is not None
    # Note that ESPHome includes the EntityInfo type in the unique id
    # as this is not a 1:1 mapping to the entity platform (ie. text_sensor)
    assert entry.unique_id == "11:22:33:44:55:AA-sensor-mysensor"
    assert entry.entity_category is None