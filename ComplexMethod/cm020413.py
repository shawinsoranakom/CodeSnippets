async def test_several_covers(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 3 covers."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0b1400cd0213c7f20d010f51": {},
            "0A1400ADF394AB010D0060": {},
            "09190000009ba8010100": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("cover.lightwaverf_siemens_0213c7_242")
    assert state
    assert state.state == "closed"
    assert state.attributes.get("friendly_name") == "LightwaveRF, Siemens 0213c7:242"

    state = hass.states.get("cover.lightwaverf_siemens_f394ab_1")
    assert state
    assert state.state == "closed"
    assert state.attributes.get("friendly_name") == "LightwaveRF, Siemens f394ab:1"

    state = hass.states.get("cover.rollertrol_009ba8_1")
    assert state
    assert state.state == "closed"
    assert state.attributes.get("friendly_name") == "RollerTrol 009ba8:1"