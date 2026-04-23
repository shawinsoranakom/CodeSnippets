async def test_supervisor_discovery_addon_not_installed(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_not_installed: AsyncMock,
    install_addon: AsyncMock,
    addon_info: AsyncMock,
    addon_store_info: AsyncMock,
    start_addon: AsyncMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test discovery with add-on not installed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(
            config=ADDON_DISCOVERY_INFO,
            name="Matter Server",
            slug=ADDON_SLUG,
            uuid="1234",
        ),
    )

    assert addon_info.call_count == 0
    assert addon_store_info.call_count == 0
    assert result["step_id"] == "hassio_confirm"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert addon_info.call_count == 0
    assert addon_store_info.call_count == 1
    assert result["step_id"] == "install_addon"
    assert result["type"] is FlowResultType.SHOW_PROGRESS

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert install_addon.call_args == call("core_matter_server")
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert start_addon.call_args == call("core_matter_server")
    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Matter"
    assert result["data"] == {
        "url": "ws://host1:5581/ws",
        "use_addon": True,
        "integration_created_addon": True,
    }
    assert setup_entry.call_count == 1