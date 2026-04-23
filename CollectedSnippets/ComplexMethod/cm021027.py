async def test_climate_entity_with_inf_value(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_generic_device_entry: MockGenericDeviceEntryType,
) -> None:
    """Test a generic climate entity with infinite temp."""
    entity_info = [
        ClimateInfo(
            object_id="myclimate",
            key=1,
            name="my climate",
            feature_flags=ClimateFeature.SUPPORTS_CURRENT_TEMPERATURE
            | ClimateFeature.SUPPORTS_TWO_POINT_TARGET_TEMPERATURE
            | ClimateFeature.SUPPORTS_CURRENT_HUMIDITY
            | ClimateFeature.SUPPORTS_TARGET_HUMIDITY
            | ClimateFeature.SUPPORTS_ACTION,
            visual_min_temperature=10.0,
            visual_max_temperature=30.0,
            visual_min_humidity=10.1,
            visual_max_humidity=29.7,
        )
    ]
    states = [
        ClimateState(
            key=1,
            mode=ClimateMode.AUTO,
            action=ClimateAction.COOLING,
            current_temperature=math.inf,
            target_temperature=math.inf,
            fan_mode=ClimateFanMode.AUTO,
            swing_mode=ClimateSwingMode.BOTH,
            current_humidity=math.inf,
            target_humidity=25.7,
        )
    ]
    await mock_generic_device_entry(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )
    state = hass.states.get("climate.test_my_climate")
    assert state is not None
    assert state.state == HVACMode.AUTO
    attributes = state.attributes
    assert ATTR_CURRENT_HUMIDITY not in attributes
    assert attributes[ATTR_HUMIDITY] == 26
    assert attributes[ATTR_MAX_HUMIDITY] == 30
    assert attributes[ATTR_MIN_HUMIDITY] == 10
    assert attributes[ATTR_TEMPERATURE] is None
    assert attributes[ATTR_CURRENT_TEMPERATURE] is None