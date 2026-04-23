async def test_one_light(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 1 light."""
    entry_data = create_rfx_test_cfg(devices={"0b1100cd0213c7f210020f51": {}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.ac_213c7f2_16")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "AC 213c7f2:16"

    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.ac_213c7f2_16"}, blocking=True
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "on"
    assert state.attributes.get("brightness") == 255

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.ac_213c7f2_16"}, blocking=True
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "off"
    assert state.attributes.get("brightness") is None

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.ac_213c7f2_16", "brightness": 100},
        blocking=True,
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "on"
    assert state.attributes.get("brightness") == 100

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.ac_213c7f2_16", "brightness": 10},
        blocking=True,
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "on"
    assert state.attributes.get("brightness") == 10

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.ac_213c7f2_16", "brightness": 255},
        blocking=True,
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "on"
    assert state.attributes.get("brightness") == 255

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.ac_213c7f2_16"}, blocking=True
    )
    state = hass.states.get("light.ac_213c7f2_16")
    assert state.state == "off"
    assert state.attributes.get("brightness") is None

    assert rfxtrx.transport.send.mock_calls == [
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x01\x00\x00")),
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x00\x00\x00")),
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x02\x06\x00")),
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x02\x00\x00")),
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x02\x0f\x00")),
        call(bytearray(b"\x0b\x11\x00\x00\x02\x13\xc7\xf2\x10\x00\x00\x00")),
    ]