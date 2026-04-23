async def test_async_step_bluetooth_valid_device_legacy_encryption_wrong_key(
    hass: HomeAssistant,
) -> None:
    """Test discovery via bluetooth with a valid device, with legacy encryption and invalid key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=YLKG07YL_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "get_encryption_key_legacy"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aaaaaaaaaaaaaaaaaaaaaaaa"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "get_encryption_key_legacy"
    assert result2["errors"]["bindkey"] == "decryption_failed"

    # Test can finish flow
    with patch(
        "homeassistant.components.xiaomi_ble.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "b853075158487ca39a5b5ea9"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Dimmer Switch 988B (YLKG07YL/YLKG08YL)"
    assert result2["data"] == {"bindkey": "b853075158487ca39a5b5ea9"}
    assert result2["result"].unique_id == "F8:24:41:C5:98:8B"