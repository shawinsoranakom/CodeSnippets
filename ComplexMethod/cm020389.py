async def test_off_delay(hass: HomeAssistant, rfxtrx, timestep) -> None:
    """Test with discovery."""
    entry_data = create_rfx_test_cfg(
        devices={"0b1100100118cdea02010f70": {"off_delay": 5}}
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == STATE_UNKNOWN

    await rfxtrx.signal("0b1100100118cdea02010f70")
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "on"

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "on"

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "off"

    await rfxtrx.signal("0b1100100118cdea02010f70")
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "on"

    await timestep(3)
    await rfxtrx.signal("0b1100100118cdea02010f70")

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "on"

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    assert state.state == "off"