async def test_async_step_reauth_legacy_wrong_key(hass: HomeAssistant) -> None:
    """Test reauth with a bad legacy key, and that we can recover."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="F8:24:41:C5:98:8B",
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
            "F8:24:41:C5:98:8B",
            b"X0\xb6\x03\xd2\x8b\x98\xc5A$\xf8\xc3I\x14vu~\x00\x00\x00\x99",
        ),
        BluetoothChange.ADVERTISEMENT,
    )

    await hass.async_block_till_done()

    results = hass.config_entries.flow.async_progress()
    assert len(results) == 1
    result = results[0]

    assert result["step_id"] == "get_encryption_key_legacy"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "b85307515a487ca39a5b5ea9"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result["step_id"] == "get_encryption_key_legacy"
    assert result2["errors"]["bindkey"] == "decryption_failed"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "b853075158487ca39a5b5ea9"},
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"