async def test_async_step_bluetooth_valid_device_encryption_wrong_key(
    hass: HomeAssistant,
) -> None:
    """Test discovery via bluetooth with a valid device, with encryption and invalid key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEMP_HUMI_ENCRYPTED_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "get_encryption_key"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "get_encryption_key"
    assert result2["errors"]["bindkey"] == "decryption_failed"

    # Test can finish flow
    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "TEST DEVICE 80A5"
    assert result2["data"] == {"bindkey": "231d39c1d7cc1ab1aee224cd096db932"}
    assert result2["result"].unique_id == "54:48:E6:8F:80:A5"