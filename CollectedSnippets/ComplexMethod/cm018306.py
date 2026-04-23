async def test_services(
    hass: HomeAssistant,
    command_store: CommandStore,
    device: Device,
    service: str,
    service_data: dict[str, Any],
    device_state: dict[str, Any],
    expected_state: str,
    expected_percentage: int | None,
    expected_preset_mode: str | None,
) -> None:
    """Test fan services."""
    entity_id = "fan.test"
    await setup_integration(hass)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_PERCENTAGE] == 18
    assert state.attributes[ATTR_PERCENTAGE_STEP] == pytest.approx(2.040816)
    assert state.attributes[ATTR_PRESET_MODES] == ["Auto"]
    assert state.attributes[ATTR_PRESET_MODE] is None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 57

    await hass.services.async_call(
        FAN_DOMAIN,
        service,
        {"entity_id": entity_id, **service_data},
        blocking=True,
    )
    await hass.async_block_till_done()

    await command_store.trigger_observe_callback(
        hass,
        device,
        {ROOT_AIR_PURIFIER: [device_state]},
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == expected_state
    assert state.attributes[ATTR_PERCENTAGE] == expected_percentage
    assert state.attributes[ATTR_PRESET_MODE] == expected_preset_mode