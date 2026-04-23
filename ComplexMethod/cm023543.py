async def test_user_setup_wolock_or_bot(hass: HomeAssistant) -> None:
    """Test the user initiated form for a lock."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[
            WOLOCK_SERVICE_INFO,
            WOHAND_SERVICE_ALT_ADDRESS_INFO,
        ],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_device"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "encrypted_choose_method"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "encrypted_key"}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "encrypted_key"
    assert result["errors"] == {}

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