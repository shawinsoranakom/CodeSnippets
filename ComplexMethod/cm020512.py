async def test_manual_port_override_invalid(
    hass: HomeAssistant, mock_connect: AsyncMock, mock_discovery: AsyncMock
) -> None:
    """Test manually setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: f"{IP_ADDRESS}:foo"}
    )
    await hass.async_block_till_done()

    mock_discovery["discover_single"].assert_called_once_with(
        IP_ADDRESS, credentials=None, port=None
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEFAULT_ENTRY_TITLE
    assert result2["data"] == CREATE_ENTRY_DATA_KLAP
    assert result2["context"]["unique_id"] == MAC_ADDRESS