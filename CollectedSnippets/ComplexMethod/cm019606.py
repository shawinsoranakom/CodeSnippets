async def test_addon_running_already_configured(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_running: AsyncMock,
    addon_info: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test that only one instance is allowed when add-on is running."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "url": "ws://localhost:5580/ws",
        },
        title="Matter",
    )
    entry.add_to_hass(hass)

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
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfiguration_successful"
    assert entry.data["url"] == "ws://host1:5581/ws"
    assert entry.title == "Matter"
    assert setup_entry.call_count == 1