async def test_entry_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_waqi: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    mock_waqi.get_by_ip.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    assert result["step_id"] == "user"

    mock_waqi.get_by_ip.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY