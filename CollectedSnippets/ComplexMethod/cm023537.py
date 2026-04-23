async def test_user_setup_wocurtain_or_bot_with_password(hass: HomeAssistant) -> None:
    """Test the user initiated form and valid address and a bot with a password."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[
            WOCURTAIN_SERVICE_INFO,
            WOHAND_ENCRYPTED_SERVICE_INFO,
            WOHAND_SERVICE_INFO_NOT_CONNECTABLE,
        ],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_device"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: "798A8547-2A3D-C609-55FF-73FA824B923B"},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "password"
    assert result2["errors"] is None

    with patch_async_setup_entry() as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PASSWORD: "abc123"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Bot 923B"
    assert result3["data"] == {
        CONF_ADDRESS: "798A8547-2A3D-C609-55FF-73FA824B923B",
        CONF_PASSWORD: "abc123",
        CONF_SENSOR_TYPE: "bot",
    }

    assert len(mock_setup_entry.mock_calls) == 1