async def test_several_lights(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 3 lights."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0b1100cd0213c7f230020f71": {},
            "0b1100100118cdea02020f70": {},
            "0b1100101118cdea02050f70": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("light.ac_213c7f2_48")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:48"

    state = hass.states.get("light.ac_118cdea_2")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 118cdea:2"

    state = hass.states.get("light.ac_1118cdea_2")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 1118cdea:2"

    await rfxtrx.signal("0b1100cd0213c7f230010f71")
    state = hass.states.get("light.ac_213c7f2_48")
    assert state
    assert state.state == "on"

    await rfxtrx.signal("0b1100cd0213c7f230000f71")
    state = hass.states.get("light.ac_213c7f2_48")
    assert state
    assert state.state == "off"

    await rfxtrx.signal("0b1100cd0213c7f230020f71")
    state = hass.states.get("light.ac_213c7f2_48")
    assert state
    assert state.state == "on"
    assert state.attributes.get("brightness") == 255