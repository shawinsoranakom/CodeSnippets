async def test_async_step_reauth_v4_wrong_key(hass: HomeAssistant) -> None:
    """Test reauth for v4 with a bad key, and that we can recover."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:EF:44:E3:9C:BC",
    )
    entry.add_to_hass(hass)
    saved_callback = None

    def _async_register_callback(_hass, _callback, _matcher, _mode):
        nonlocal saved_callback
        saved_callback = _callback
        return lambda: None

    with patch(
        "homeassistant.components.bluetooth.update_coordinator.async_register_callback",
        _async_register_callback,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 0

    # WARNING: This test data is synthetic, rather than captured from a real device
    # obj type is 0x1310, payload len is 0x2 and payload is 0x6000
    saved_callback(
        make_advertisement(
            "54:EF:44:E3:9C:BC",
            b"XY\x97\tf\xbc\x9c\xe3D\xefT\x01\x08\x12\x05\x00\x00\x00q^\xbe\x90",
        ),
        BluetoothChange.ADVERTISEMENT,
    )

    await hass.async_block_till_done()

    results = hass.config_entries.flow.async_progress()
    assert len(results) == 1
    result = results[0]

    assert result["step_id"] == "get_encryption_key_4_5_choose_method"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "get_encryption_key_4_5"},
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"bindkey": "5b51a7c91cde6707c9ef18dada143a58"},
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "get_encryption_key_4_5"
    assert result3["errors"]["bindkey"] == "decryption_failed"

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        user_input={"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"},
    )
    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "reauth_successful"