async def test_errors(
    hass: HomeAssistant, exc: Exception, base_error: str, mock_brother_client: AsyncMock
) -> None:
    """Test connection to host error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_brother_client.async_update.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}

    mock_brother_client.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HL-L2340DW 0123456789"
    assert result["data"][CONF_HOST] == "127.0.0.1"
    assert result["data"][CONF_TYPE] == "laser"
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT] == 161
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY] == "public"
    assert result["result"].unique_id == "0123456789"