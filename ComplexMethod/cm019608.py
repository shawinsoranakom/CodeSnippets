async def test_addon_installed_failures(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_installed: AsyncMock,
    addon_info: AsyncMock,
    start_addon: AsyncMock,
    get_addon_discovery_info: AsyncMock,
    client_connect: AsyncMock,
    start_addon_error: Exception | None,
    client_connect_error: Exception | None,
    discovery_info_called: bool,
    client_connect_called: bool,
) -> None:
    """Test add-on start failure when add-on is installed."""
    start_addon.side_effect = start_addon_error
    client_connect.side_effect = client_connect_error

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert addon_info.call_count == 1
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert start_addon.call_args == call("core_matter_server")
    assert get_addon_discovery_info.called is discovery_info_called
    assert client_connect.called is client_connect_called
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_start_failed"