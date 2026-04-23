async def test_rssi_sensor(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 1 sensor."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0913000022670e013b70": {
                "data_bits": 4,
                "command_on": 0xE,
                "command_off": 0x7,
            },
            "0b1100cd0213c7f230010f71": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("sensor.pt2262_226700_signal_strength")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == "PT2262 226700 Signal strength"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    state = hass.states.get("sensor.ac_213c7f2_48_signal_strength")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == "AC 213c7f2:48 Signal strength"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    await rfxtrx.signal("0913000022670e013b70")
    await rfxtrx.signal("0b1100cd0213c7f230010f71")

    state = hass.states.get("sensor.pt2262_226700_signal_strength")
    assert state
    assert state.state == "-64"

    state = hass.states.get("sensor.ac_213c7f2_48_signal_strength")
    assert state
    assert state.state == "-64"

    await rfxtrx.signal("0913000022670e013b60")
    await rfxtrx.signal("0b1100cd0213c7f230010f61")

    state = hass.states.get("sensor.pt2262_226700_signal_strength")
    assert state
    assert state.state == "-72"

    state = hass.states.get("sensor.ac_213c7f2_48_signal_strength")
    assert state
    assert state.state == "-72"