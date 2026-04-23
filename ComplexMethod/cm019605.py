async def test_addon_running_failures(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_running: AsyncMock,
    addon_info: AsyncMock,
    get_addon_discovery_info: AsyncMock,
    client_connect: AsyncMock,
    discovery_info_error: Exception | None,
    client_connect_error: Exception | None,
    addon_info_error: Exception | None,
    abort_reason: str,
    discovery_info_called: bool,
    client_connect_called: bool,
) -> None:
    """Test all failures when add-on is running."""
    get_addon_discovery_info.side_effect = discovery_info_error
    client_connect.side_effect = client_connect_error
    addon_info.side_effect = addon_info_error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert addon_info.call_count == 1
    assert get_addon_discovery_info.called is discovery_info_called
    assert client_connect.called is client_connect_called
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == abort_reason