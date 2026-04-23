async def test_discovery_success(
    hass: HomeAssistant, mock_discover, mock_setup_entry
) -> None:
    """Verify discovery finds devices and completes config entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )
    assert result["type"] == FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_discovery"
    assert result["progress_action"] == "start_discovery"

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "choose_switch"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SWITCH_LIST: "192.168.1.100"}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{DEFAULT_NAME} (192.168.1.100)"
    assert result["data"][CONF_HOST] == "192.168.1.100"
    assert result["data"][CONF_MAC] == "ac:cf:23:12:34:56"
    assert result["result"].unique_id == "ac:cf:23:12:34:56"