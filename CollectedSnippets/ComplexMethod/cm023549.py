async def test_user_cloud_login_then_encrypted_device(hass: HomeAssistant) -> None:
    """Test cloud login followed by encrypted device setup using saved credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "cloud_login"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_login"

    with (
        patch(
            "homeassistant.components.switchbot.config_flow.fetch_cloud_devices",
            return_value=None,
        ),
        patch(
            "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
            return_value=[WOLOCK_SERVICE_INFO],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpass",
            },
        )

    # Should go to encrypted device choice menu
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    # Choose encrypted auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_auth"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_auth"

    # Simulate the user navigating away and re-opening the dialog.
    # The failed auto-auth cleared credentials, so calling with None now
    # redirects back to the method selection menu.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        None,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    # User selects encrypted_auth again and manually enters credentials
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_auth"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_auth"

    with (
        patch_async_setup_entry() as mock_setup_entry,
        patch(
            "switchbot.SwitchbotLock.async_retrieve_encryption_key",
            return_value={
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
        ),
        patch("switchbot.SwitchbotLock.verify_encryption_key", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpass",
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