async def test_bluetooth_discovery_encrypted_key(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a lock."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=WOLOCK_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_key"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_key"
    assert result["errors"] == {}

    with patch(
        "switchbot.SwitchbotLock.verify_encryption_key",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEY_ID: "",
                CONF_ENCRYPTION_KEY: "",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_key"
    assert result["errors"] == {"base": "encryption_key_invalid"}

    with (
        patch_async_setup_entry() as mock_setup_entry,
        patch(
            "switchbot.SwitchbotLock.verify_encryption_key",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Lock EEFF"
    assert result["data"] == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_KEY_ID: "ff",
        CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
        CONF_SENSOR_TYPE: "lock",
    }

    assert len(mock_setup_entry.mock_calls) == 1