async def test_user_setup_worelay_switch_1pm_auth_switchbot_api_down(
    hass: HomeAssistant,
) -> None:
    """Test the user initiated form for a relay switch 1pm when the switchbot api is down."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[WORELAY_SWITCH_1PM_SERVICE_INFO],
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
    assert result["errors"] == {}

    with patch(
        "switchbot.SwitchbotRelaySwitch.async_retrieve_encryption_key",
        side_effect=SwitchbotAccountConnectionError("Switchbot API down"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "",
                CONF_PASSWORD: "",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "api_error"
    assert result["description_placeholders"] == {"error_detail": "Switchbot API down"}