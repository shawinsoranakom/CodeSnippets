async def test_manual_already_configured(
    hass: HomeAssistant,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test manual step abort if already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"url": "ws://host1:5581/ws"}, title="Matter"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:5580/ws",
        },
    )
    await hass.async_block_till_done()

    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfiguration_successful"
    assert entry.data["url"] == "ws://localhost:5580/ws"
    assert entry.data["use_addon"] is False
    assert entry.data["integration_created_addon"] is False
    assert entry.title == "Matter"
    assert setup_entry.call_count == 1