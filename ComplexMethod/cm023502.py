async def test_async_step_reauth_wrong_key(hass: HomeAssistant) -> None:
    """Test reauth with a bad key, and that we can recover."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
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

    saved_callback(TEMP_HUMI_ENCRYPTED_SERVICE_INFO, BluetoothChange.ADVERTISEMENT)
    await hass.async_block_till_done()

    results = hass.config_entries.flow.async_progress()
    assert len(results) == 1
    result = results[0]

    assert result["step_id"] == "get_encryption_key"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "5b51a7c91cde6707c9ef18dada143a58"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "get_encryption_key"
    assert result2["errors"]["bindkey"] == "decryption_failed"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"