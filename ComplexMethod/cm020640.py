async def test_async_step_user_with_found_devices_v4_encryption_wrong_key(
    hass: HomeAssistant,
) -> None:
    """Test setup from service info cache with devices found, with v4 encryption and wrong key."""
    # Get a list of devices
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.async_discovered_service_info",
        return_value=[JTYJGD03MI_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Pick a device
    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "54:EF:44:E3:9C:BC"},
    )
    assert result1["type"] is FlowResultType.MENU
    assert result1["step_id"] == "get_encryption_key_4_5_choose_method"

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        user_input={"next_step_id": "get_encryption_key_4_5"},
    )

    # Try an incorrect key
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"bindkey": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "get_encryption_key_4_5"
    assert result3["errors"]["bindkey"] == "decryption_failed"

    # Check can still finish flow
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