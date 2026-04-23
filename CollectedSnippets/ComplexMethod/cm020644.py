async def test_async_step_user_with_found_devices_legacy_encryption_wrong_key_length(
    hass: HomeAssistant,
) -> None:
    """Test setup from service info cache with devices found, with legacy encryption and wrong key length."""
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.async_discovered_service_info",
        return_value=[YLKG07YL_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "F8:24:41:C5:98:8B"},
    )
    assert result1["type"] is FlowResultType.FORM
    assert result1["step_id"] == "get_encryption_key_legacy"

    # Enter an incorrect code
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "b85307518487ca39a5b5ea9"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "get_encryption_key_legacy"
    assert result2["errors"]["bindkey"] == "expected_24_characters"

    # Check you can finish the flow
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