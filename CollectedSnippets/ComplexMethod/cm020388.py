async def test_several(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 3."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0b1100cd0213c7f230010f71": {},
            "0b1100100118cdea02010f70": {},
            "0b1100100118cdea03010f70": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.ac_213c7f2_48")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:48"

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 118cdea:2"

    state = hass.states.get("binary_sensor.ac_118cdea_3")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 118cdea:3"

    # "2: Group on"
    await rfxtrx.signal("0b1100100118cdea03040f70")
    assert hass.states.get("binary_sensor.ac_118cdea_2").state == "on"
    assert hass.states.get("binary_sensor.ac_118cdea_3").state == "on"

    # "2: Group off"
    await rfxtrx.signal("0b1100100118cdea03030f70")
    assert hass.states.get("binary_sensor.ac_118cdea_2").state == "off"
    assert hass.states.get("binary_sensor.ac_118cdea_3").state == "off"