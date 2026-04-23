async def test_climate(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    setup_integration: None,
) -> None:
    """Test climate temperature & preset."""

    # Set temperature
    mqtt_mock.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: _CLIMATE_ENTITY_ID,
            ATTR_TEMPERATURE: _SET_TEMPERATURE,
        },
        blocking=True,
    )

    mqtt_mock.async_publish.assert_called_once_with(
        _TOPIC_CLIMATE_SET_STATE, _PAYLOAD_CLIMATE_SET_TEMP, 0, False
    )

    # Simulate a partial state response
    async_fire_mqtt_message(hass, _TOPIC_CLIMATE_STATE, _PAYLOAD_CLIMATE_STATE_TEMP)
    await hass.async_block_till_done()

    # Check state
    entity = hass.states.get(_CLIMATE_ENTITY_ID)
    assert entity
    assert entity.attributes[ATTR_TEMPERATURE] == _SET_TEMPERATURE
    assert entity.attributes[ATTR_CURRENT_TEMPERATURE] is None
    assert entity.attributes[ATTR_PRESET_MODE] == "MANUEEL"
    assert entity.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert entity.state == HVACMode.HEAT

    # After a delay, a full state request should've been sent
    _wait_and_assert_state_request(hass, mqtt_mock)

    # Simulate a full state response
    async_fire_mqtt_message(
        hass, _TOPIC_CLIMATE_STATE, _PAYLOAD_CLIMATE_STATE_TEMP_FULL
    )
    await hass.async_block_till_done()

    # Check state after full state response
    entity = hass.states.get(_CLIMATE_ENTITY_ID)
    assert entity
    assert entity.attributes[ATTR_TEMPERATURE] == _SET_TEMPERATURE
    assert entity.attributes[ATTR_CURRENT_TEMPERATURE] == _CURRENT_TEMPERATURE
    assert entity.attributes[ATTR_PRESET_MODE] == "MANUEEL"
    assert entity.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert entity.state == HVACMode.HEAT

    # Set preset
    mqtt_mock.reset_mock()
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: _CLIMATE_ENTITY_ID,
            ATTR_PRESET_MODE: _REGIME,
        },
        blocking=True,
    )

    mqtt_mock.async_publish.assert_called_once_with(
        _TOPIC_CLIMATE_SET_STATE, _PAYLOAD_CLIMATE_SET_PRESET, 0, False
    )

    # Simulate a partial state response
    async_fire_mqtt_message(hass, _TOPIC_CLIMATE_STATE, _PAYLOAD_CLIMATE_STATE_PRESET)
    await hass.async_block_till_done()

    # Check state
    entity = hass.states.get(_CLIMATE_ENTITY_ID)
    assert entity
    assert entity.attributes[ATTR_TEMPERATURE] == _SET_TEMPERATURE
    assert entity.attributes[ATTR_CURRENT_TEMPERATURE] == _CURRENT_TEMPERATURE
    assert entity.attributes[ATTR_PRESET_MODE] == _REGIME
    assert entity.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert entity.state == HVACMode.HEAT

    # After a delay, a full state request should've been sent
    _wait_and_assert_state_request(hass, mqtt_mock)

    # Simulate a full state response
    async_fire_mqtt_message(
        hass, _TOPIC_CLIMATE_STATE, _PAYLOAD_CLIMATE_STATE_PRESET_FULL
    )
    await hass.async_block_till_done()

    # Check state after full state response
    entity = hass.states.get(_CLIMATE_ENTITY_ID)
    assert entity
    assert entity.attributes[ATTR_TEMPERATURE] == 22.0
    assert entity.attributes[ATTR_CURRENT_TEMPERATURE] == _CURRENT_TEMPERATURE
    assert entity.attributes[ATTR_PRESET_MODE] == _REGIME
    assert entity.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    assert entity.state == HVACMode.HEAT