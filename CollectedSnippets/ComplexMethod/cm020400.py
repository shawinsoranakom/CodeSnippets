async def test_one_chime(hass: HomeAssistant, rfxtrx, timestep) -> None:
    """Test with 1 entity."""
    entry_data = create_rfx_test_cfg(
        devices={"0a16000000000000000000": {"off_delay": 2.0}}
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    entity_id = "siren.byron_sx_00_00"

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"
    assert state.attributes.get("friendly_name") == "Byron SX 00:00"

    await hass.services.async_call(
        "siren", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await timestep(5)

    state = hass.states.get(entity_id)
    assert state.state == "off"

    await hass.services.async_call(
        "siren", "turn_on", {"entity_id": entity_id, "tone": "Sound 1"}, blocking=True
    )
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await timestep(3)

    state = hass.states.get(entity_id)
    assert state.state == "off"

    await rfxtrx.signal("0a16000000000000000000")
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await timestep(3)

    state = hass.states.get(entity_id)
    assert state.state == "off"

    assert rfxtrx.transport.send.mock_calls == [
        call(bytearray(b"\x07\x16\x00\x00\x00\x00\x00\x00")),
        call(bytearray(b"\x07\x16\x00\x00\x00\x00\x01\x00")),
    ]