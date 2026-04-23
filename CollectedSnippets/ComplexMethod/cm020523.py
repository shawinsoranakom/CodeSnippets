async def test_discovery_timeout_try_connect_all(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test discovery tries legacy connect on timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_discovery["discover_single"].side_effect = TimeoutError
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]
    assert mock_connect["connect"].call_count == 0

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: IP_ADDRESS}
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["context"]["unique_id"] == MAC_ADDRESS
    assert mock_connect["connect"].call_count == 1