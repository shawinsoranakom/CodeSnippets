async def test_async_step_bluetooth_valid_device_v4_encryption_wrong_key_length(
    hass: HomeAssistant,
) -> None:
    """Test discovery via bluetooth with a valid device, with v4 encryption and wrong key length."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JTYJGD03MI_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "get_encryption_key_4_5_choose_method"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "get_encryption_key_4_5"},
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"bindkey": "5b51a7c91cde6707c9ef18fda143a58"},
    )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "get_encryption_key_4_5"
    assert result3["errors"]["bindkey"] == "expected_32_characters"

    # Test can finish flow
    with patch(
        "homeassistant.components.xiaomi_ble.async_setup_entry", return_value=True
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            user_input={"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"},
        )

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Smoke Detector 9CBC (JTYJGD03MI)"
    assert result4["data"] == {"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"}
    assert result4["result"].unique_id == "54:EF:44:E3:9C:BC"