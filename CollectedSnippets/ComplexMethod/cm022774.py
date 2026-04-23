async def test_water_heater_off_mode_on_off(
    hass: HomeAssistant, hk_driver: HomeDriver, events: list[Event]
) -> None:
    """Test water heater Off mode via ON_OFF feature."""
    entity_id = "water_heater.test"

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {ATTR_SUPPORTED_FEATURES: WaterHeaterEntityFeature.ON_OFF},
    )
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    # Verify Off is exposed as a valid mode
    valid_values = acc.char_target_heat_cool.properties.get("ValidValues", {})
    assert valid_values == {"Off": 0, "Heat": 1}

    # Set to Off from HomeKit
    call_turn_off = async_mock_service(hass, WATER_HEATER_DOMAIN, "turn_off")

    acc.char_target_heat_cool.client_update_value(0)
    await hass.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "off"

    # Set to Heat from HomeKit
    call_turn_on = async_mock_service(hass, WATER_HEATER_DOMAIN, "turn_on")

    acc.char_target_heat_cool.client_update_value(1)
    await hass.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "on"

    # Update HA state to off and verify HomeKit reflects it
    hass.states.async_set(
        entity_id,
        "off",
        {ATTR_SUPPORTED_FEATURES: WaterHeaterEntityFeature.ON_OFF},
    )
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_OFF
    assert acc.char_current_heat_cool.value == HC_HEAT_COOL_OFF

    # Update HA state back to heat and verify HomeKit reflects it
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {ATTR_SUPPORTED_FEATURES: WaterHeaterEntityFeature.ON_OFF},
    )
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT
    assert acc.char_current_heat_cool.value == HC_HEAT_COOL_HEAT