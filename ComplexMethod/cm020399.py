async def test_pt2262_switch_events(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 1 PT2262 switch."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0913000022670e013970": {
                "data_bits": 4,
                "command_on": 0xE,
                "command_off": 0x7,
            }
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.pt2262_226700")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "PT2262 226700"

    # "Command: 0xE"
    await rfxtrx.signal("0913000022670e013970")
    assert hass.states.get("switch.pt2262_226700").state == "on"

    # "Command: 0x0"
    await rfxtrx.signal("09130000226700013970")
    assert hass.states.get("switch.pt2262_226700").state == "on"

    # "Command: 0x7"
    await rfxtrx.signal("09130000226707013d70")
    assert hass.states.get("switch.pt2262_226700").state == "off"

    # "Command: 0x1"
    await rfxtrx.signal("09130000226701013d70")
    assert hass.states.get("switch.pt2262_226700").state == "off"