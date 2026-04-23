async def test_water_heater_off_mode_operation_mode(
    hass: HomeAssistant, hk_driver: HomeDriver, events: list[Event]
) -> None:
    """Test water heater Off mode via OPERATION_MODE feature."""
    entity_id = "water_heater.test"

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_SUPPORTED_FEATURES: WaterHeaterEntityFeature.OPERATION_MODE,
            ATTR_OPERATION_LIST: ["off", "electric", "gas"],
        },
    )
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    # Verify Off is exposed as a valid mode
    valid_values = acc.char_target_heat_cool.properties.get("ValidValues", {})
    assert valid_values == {"Off": 0, "Heat": 1}

    # Set to Off from HomeKit — should call set_operation_mode
    call_set_op = async_mock_service(hass, WATER_HEATER_DOMAIN, "set_operation_mode")

    acc.char_target_heat_cool.client_update_value(0)
    await hass.async_block_till_done()
    assert call_set_op
    assert call_set_op[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_op[0].data["operation_mode"] == "off"
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "off"

    # Set to Heat from HomeKit — should pick first non-off operation mode
    call_set_op.clear()

    acc.char_target_heat_cool.client_update_value(1)
    await hass.async_block_till_done()
    assert call_set_op
    assert call_set_op[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_op[0].data["operation_mode"] == "electric"
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "electric"