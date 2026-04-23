async def test_user_setup_woencrypted_auth_unknown_error(
    hass: HomeAssistant,
) -> None:
    """Test the encrypted auth step shows unknown error for unexpected exceptions."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[WOLOCK_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_auth"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_auth"

    with patch(
        "switchbot.SwitchbotLock.async_retrieve_encryption_key",
        side_effect=Exception("Unexpected network failure"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user@example.com",
                CONF_PASSWORD: "password",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_auth"
    assert result["errors"] == {"base": "unknown"}

    # Recover: re-submit with valid credentials and successful key retrieval
    with (
        patch_async_setup_entry() as mock_setup_entry,
        patch(
            "switchbot.SwitchbotLock.verify_encryption_key",
            return_value=True,
        ),
        patch(
            "switchbot.SwitchbotLock.async_retrieve_encryption_key",
            return_value={
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "user@example.com",
                CONF_PASSWORD: "password",
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