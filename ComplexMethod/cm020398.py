async def test_switch_events(hass: HomeAssistant, rfxtrx) -> None:
    """Event test with 2 switches."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0b1100cd0213c7f205010f51": {},
            "0b1100cd0213c7f210010f51": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.ac_213c7f2_16")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:16"

    state = hass.states.get("switch.ac_213c7f2_5")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:5"

    # "16: On"
    await rfxtrx.signal("0b1100100213c7f210010f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == STATE_UNKNOWN
    assert hass.states.get("switch.ac_213c7f2_16").state == "on"

    # "16: Off"
    await rfxtrx.signal("0b1100100213c7f210000f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == STATE_UNKNOWN
    assert hass.states.get("switch.ac_213c7f2_16").state == "off"

    # "5: On"
    await rfxtrx.signal("0b1100100213c7f205010f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == "on"
    assert hass.states.get("switch.ac_213c7f2_16").state == "off"

    # "5: Off"
    await rfxtrx.signal("0b1100100213c7f205000f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == "off"
    assert hass.states.get("switch.ac_213c7f2_16").state == "off"

    # "16: Group on"
    await rfxtrx.signal("0b1100100213c7f210040f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == "on"
    assert hass.states.get("switch.ac_213c7f2_16").state == "on"

    # "16: Group off"
    await rfxtrx.signal("0b1100100213c7f210030f70")
    assert hass.states.get("switch.ac_213c7f2_5").state == "off"
    assert hass.states.get("switch.ac_213c7f2_16").state == "off"