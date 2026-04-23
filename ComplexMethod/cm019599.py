async def test_zeroconf_not_onboarded_not_installed(
    hass: HomeAssistant,
    addon_info: AsyncMock,
    addon_store_info: AsyncMock,
    install_addon: AsyncMock,
    start_addon: AsyncMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
    zeroconf_info: ZeroconfServiceInfo,
) -> None:
    """Test flow Zeroconf discovery when not onboarded and add-on not installed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=zeroconf_info,
    )
    await hass.async_block_till_done()

    assert addon_info.call_count == 0
    assert addon_store_info.call_count == 1
    assert install_addon.call_args == call("core_matter_server")
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