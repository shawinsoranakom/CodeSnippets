async def test_humidifier_missing_mode(
    hass: HomeAssistant, client, climate_adc_t3000_missing_mode, integration
) -> None:
    """Test a humidity control command class entity."""

    node = climate_adc_t3000_missing_mode

    # Test that de-humidifer entity does not exist but humidifier entity does
    entity_id = "humidifier.adc_t3000_missing_mode_dehumidifier"
    state = hass.states.get(entity_id)
    assert not state

    entity_id = "humidifier.adc_t3000_missing_mode_humidifier"
    state = hass.states.get(entity_id)
    assert state

    client.async_send_command.reset_mock()

    # Test turning off when device is previously auto for a device which does not have de-humidify mode
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Humidity Control Mode",
                "commandClass": CommandClass.HUMIDITY_CONTROL_MODE,
                "endpoint": 0,
                "property": "mode",
                "propertyName": "mode",
                "newValue": int(HumidityControlMode.AUTO),
                "prevValue": int(HumidityControlMode.OFF),
            },
        },
    )
    node.receive_event(event)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 68
    assert args["valueId"] == {
        "commandClass": CommandClass.HUMIDITY_CONTROL_MODE,
        "endpoint": 0,
        "property": "mode",
    }
    assert args["value"] == int(HumidityControlMode.OFF)

    client.async_send_command.reset_mock()