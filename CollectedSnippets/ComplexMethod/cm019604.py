async def test_addon_running(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_running: AsyncMock,
    addon_info: AsyncMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test add-on already running on Supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )
    await hass.async_block_till_done()

    assert addon_info.call_count == 1
    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Matter"
    assert result["data"] == {
        "url": "ws://host1:5581/ws",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert setup_entry.call_count == 1