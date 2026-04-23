async def test_bluetooth_discovery_incorrect_cloud_auth(
    hass: HomeAssistant,
) -> None:
    """Test discovery via bluetooth with incorrect cloud auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=JTYJGD03MI_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "get_encryption_key_4_5_choose_method"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "cloud_auth"},
    )

    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.XiaomiCloudTokenFetch.get_device_info",
        side_effect=XiaomiCloudInvalidAuthenticationException,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={"username": "x@x.x", "password": "wrong"},
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "cloud_auth"
    assert result3["errors"]["base"] == "auth_failed"

    device = XiaomiCloudBLEDevice(
        name="x",
        mac="54:EF:44:E3:9C:BC",
        bindkey="5b51a7c91cde6707c9ef18dfda143a58",
    )
    # Verify we can try again with the correct password
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.XiaomiCloudTokenFetch.get_device_info",
        return_value=device,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            user_input={"username": "x@x.x", "password": "correct"},
        )

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Smoke Detector 9CBC (JTYJGD03MI)"
    assert result4["data"] == {"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"}
    assert result4["result"].unique_id == "54:EF:44:E3:9C:BC"