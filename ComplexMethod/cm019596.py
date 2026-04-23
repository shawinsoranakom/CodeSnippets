async def test_zeroconf_discovery_not_onboarded_not_supervisor(
    hass: HomeAssistant,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
    not_onboarded: MagicMock,
    zeroconf_info: ZeroconfServiceInfo,
) -> None:
    """Test flow started from Zeroconf discovery when not onboarded."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=zeroconf_info,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:5580/ws",
        },
    )
    await hass.async_block_till_done()

    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Matter"
    assert result["data"] == {
        "url": "ws://localhost:5580/ws",
        "integration_created_addon": False,
        "use_addon": False,
    }
    assert setup_entry.call_count == 1