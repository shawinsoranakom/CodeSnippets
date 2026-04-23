async def test_turn_on_with_preset_mode_only(
    hass: HomeAssistant, fan_entity_id
) -> None:
    """Test turning on the device with a preset_mode and no speed setting."""
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_AUTO
    assert state.attributes[fan.ATTR_PRESET_MODES] == [
        PRESET_MODE_AUTO,
        PRESET_MODE_SMART,
        PRESET_MODE_SLEEP,
        PRESET_MODE_ON,
    ]

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_SMART},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_ON
    assert state.attributes[fan.ATTR_PRESET_MODE] == PRESET_MODE_SMART

    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PRESET_MODE] is None

    with pytest.raises(fan.NotValidPresetModeError) as exc:
        await hass.services.async_call(
            fan.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
    assert exc.value.translation_domain == fan.DOMAIN
    assert exc.value.translation_key == "not_valid_preset_mode"
    assert exc.value.translation_placeholders == {
        "preset_mode": "invalid",
        "preset_modes": "auto, smart, sleep, on",
    }

    state = hass.states.get(fan_entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[fan.ATTR_PRESET_MODE] is None