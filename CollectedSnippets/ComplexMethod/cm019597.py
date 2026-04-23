async def test_zeroconf_not_onboarded_already_discovered(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_info: AsyncMock,
    addon_running: AsyncMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
    not_onboarded: MagicMock,
    zeroconf_info: ZeroconfServiceInfo,
) -> None:
    """Test flow Zeroconf discovery when not onboarded and already discovered."""
    result_flow_1 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=zeroconf_info,
    )
    result_flow_2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=zeroconf_info,
    )
    await hass.async_block_till_done()
    assert result_flow_2["type"] is FlowResultType.ABORT
    assert result_flow_2["reason"] == "already_configured"
    assert addon_info.call_count == 1
    assert client_connect.call_count == 1
    assert result_flow_1["type"] is FlowResultType.CREATE_ENTRY
    assert result_flow_1["title"] == "Matter"
    assert result_flow_1["data"] == {
        "url": "ws://host1:5581/ws",
        "use_addon": True,
        "integration_created_addon": False,
    }
    assert setup_entry.call_count == 1