async def test_hvac_node_only_hvac(
    hass: HomeAssistant,
    hvac_node_only_hvac: Sensor,
    receive_message: Callable[[str], None],
    transport_write: MagicMock,
) -> None:
    """Test a hvac only hvac node."""
    entity_id = "climate.hvac_node_1_1"

    state = hass.states.get(entity_id)

    assert state
    assert state.state == HVACMode.OFF
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20.0
    assert state.attributes["supported_features"] == 384

    # Test set hvac mode heat
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;21;HeatOn\n")

    receive_message("1;1;1;0;21;HeatOn\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20.0

    transport_write.reset_mock()

    # Test set hvac mode cool
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.COOL},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;21;CoolOn\n")

    receive_message("1;1;1;0;21;CoolOn\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20.0

    transport_write.reset_mock()

    # Test set hvac mode off
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;21;Off\n")

    receive_message("1;1;1;0;21;Off\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == HVACMode.OFF