async def test_bluetooth_discovery_encrypted_auth_back_navigation(
    hass: HomeAssistant,
) -> None:
    """Test that resuming an abandoned encrypted_auth flow resets to the method menu."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=WOLOCK_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    # User selects encrypted_auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_auth"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_auth"

    # Simulate user closing dialog and re-opening: call the step with no input
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=None
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    # User can switch to encrypted_key and complete the flow
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_key"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_key"

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
    assert len(mock_setup_entry.mock_calls) == 1