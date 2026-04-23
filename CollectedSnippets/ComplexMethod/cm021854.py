async def test_hmip_power_sensor(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipPowerSensor."""
    entity_id = "sensor.flur_oben_power"
    entity_name = "Flur oben Power"
    device_model = "HmIP-BSM"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Flur oben"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "0.0"
    assert ha_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    await async_manipulate_test_data(hass, hmip_device, "currentPowerConsumption", 23.5)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == "23.5"
    # test common attributes
    assert not ha_state.attributes.get(ATTR_DEVICE_OVERHEATED)
    assert not ha_state.attributes.get(ATTR_DEVICE_OVERLOADED)
    assert not ha_state.attributes.get(ATTR_DEVICE_UNTERVOLTAGE)
    assert not ha_state.attributes.get(ATTR_DUTY_CYCLE_REACHED)
    assert not ha_state.attributes.get(ATTR_CONFIG_PENDING)
    await async_manipulate_test_data(hass, hmip_device, "deviceOverheated", True)
    await async_manipulate_test_data(hass, hmip_device, "deviceOverloaded", True)
    await async_manipulate_test_data(hass, hmip_device, "deviceUndervoltage", True)
    await async_manipulate_test_data(hass, hmip_device, "dutyCycle", True)
    await async_manipulate_test_data(hass, hmip_device, "configPending", True)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_DEVICE_OVERHEATED]
    assert ha_state.attributes[ATTR_DEVICE_OVERLOADED]
    assert ha_state.attributes[ATTR_DEVICE_UNTERVOLTAGE]
    assert ha_state.attributes[ATTR_DUTY_CYCLE_REACHED]
    assert ha_state.attributes[ATTR_CONFIG_PENDING]