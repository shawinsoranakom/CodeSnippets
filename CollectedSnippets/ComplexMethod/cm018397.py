async def test_cloud_flow_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_geniushub_client: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test cloud flow exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "cloud_api"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_api"

    mock_geniushub_client.request.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "abcdef",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_geniushub_client.request.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "abcdef",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY