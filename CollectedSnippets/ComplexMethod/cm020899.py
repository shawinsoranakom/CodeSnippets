async def test_dhcp_failed_legacy_auth(
    hass: HomeAssistant, mocked_plug: MagicMock, mocked_plug_legacy_no_auth: MagicMock
) -> None:
    """Test we can recover from failed legacy authentication during dhcp flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=CONF_DHCP_FLOW
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_discovery"
    with patch_config_flow(mocked_plug_legacy_no_auth):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"

    with patch_config_flow(mocked_plug), _patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DHCP_DATA,
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == CONF_DATA