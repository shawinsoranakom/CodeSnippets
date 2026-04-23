async def test_bluetooth_discovery_device_v4_encryption_from_cloud_wrong_key(
    hass: HomeAssistant,
) -> None:
    """Test discovery via bluetooth with a valid v4 device, with wrong auth from cloud."""
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

    device = XiaomiCloudBLEDevice(
        name="x",
        mac="54:EF:44:E3:9C:BC",
        bindkey="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    )
    with patch(
        "homeassistant.components.xiaomi_ble.config_flow.XiaomiCloudTokenFetch.get_device_info",
        return_value=device,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={"username": "x@x.x", "password": "x"},
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "get_encryption_key_4_5"
    assert result3["errors"]["bindkey"] == "decryption_failed"

    # Verify we can fallback to manual key
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