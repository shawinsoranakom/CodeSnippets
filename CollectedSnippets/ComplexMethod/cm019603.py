async def test_not_addon(
    hass: HomeAssistant,
    supervisor: MagicMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test opting out of add-on on Supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:5581/ws",
        },
    )
    await hass.async_block_till_done()

    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Matter"
    assert result["data"] == {
        "url": "ws://localhost:5581/ws",
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert setup_entry.call_count == 1