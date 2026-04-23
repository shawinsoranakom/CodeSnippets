async def test_water_heater(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test water heater entity."""
    state = hass.states.get("water_heater.water_heater")
    assert state
    assert state.attributes["min_temp"] == 40
    assert state.attributes["max_temp"] == 65
    assert state.attributes["temperature"] == 65
    assert state.attributes["operation_list"] == ["eco", "high_demand", "off"]
    assert state.state == STATE_ECO

    # test supported features correctly parsed
    mask = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.ON_OFF
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    assert state.attributes["supported_features"] & mask == mask