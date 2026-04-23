async def test_one_security1(hass: HomeAssistant, rfxtrx, timestep) -> None:
    """Test with 1 entity."""
    entry_data = create_rfx_test_cfg(devices={"08200300a109000670": {"off_delay": 2.0}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    entity_id = "siren.kd101_smoke_detector_a10900_32"

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "off"
    assert state.attributes.get("friendly_name") == "KD101 Smoke Detector a10900:32"

    await hass.services.async_call(
        "siren", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await hass.services.async_call(
        "siren", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    state = hass.states.get(entity_id)
    assert state.state == "off"

    await hass.services.async_call(
        "siren", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await timestep(11)

    state = hass.states.get(entity_id)
    assert state.state == "off"

    await rfxtrx.signal("08200300a109000670")
    state = hass.states.get(entity_id)
    assert state.state == "on"

    await rfxtrx.signal("08200300a109000770")
    state = hass.states.get(entity_id)
    assert state.state == "off"

    assert rfxtrx.transport.send.mock_calls == [
        call(bytearray(b"\x08\x20\x03\x00\xa1\x09\x00\x06\x00")),
        call(bytearray(b"\x08\x20\x03\x01\xa1\x09\x00\x07\x00")),
        call(bytearray(b"\x08\x20\x03\x02\xa1\x09\x00\x06\x00")),
    ]