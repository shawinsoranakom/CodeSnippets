async def test_room_airconditioner(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test if a climate entity is created for a Room Airconditioner device."""
    state = hass.states.get("climate.room_airconditioner")
    assert state
    assert state.attributes["current_temperature"] == 20
    # room airconditioner has mains power on OnOff cluster with value set to False
    assert state.state == HVACMode.OFF

    # test supported features correctly parsed
    # WITHOUT temperature_range support
    mask = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF
    assert state.attributes["supported_features"] & mask == mask

    # set mains power to ON (OnOff cluster)
    set_node_attribute(matter_node, 1, 6, 0, True)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.room_airconditioner")

    # test supported HVAC modes include fan and dry modes
    assert state.attributes["hvac_modes"] == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.HEAT_COOL,
    ]
    # test fan-only hvac mode
    set_node_attribute(matter_node, 1, 513, 28, 7)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.room_airconditioner")
    assert state
    assert state.state == HVACMode.FAN_ONLY

    # test dry hvac mode
    set_node_attribute(matter_node, 1, 513, 28, 8)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.room_airconditioner")
    assert state
    assert state.state == HVACMode.DRY

    # test featuremap update
    set_node_attribute(matter_node, 1, 513, 65532, 1)
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get("climate.room_airconditioner")
    assert state.attributes["supported_features"] & ClimateEntityFeature.TURN_ON