async def test_flow_exceptions(
    hass: HomeAssistant,
    mock_nsapi: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test config flow handling different exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    mock_nsapi.get_stations.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    mock_nsapi.get_stations.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Nederlandse Spoorwegen"
    assert result["data"] == {CONF_API_KEY: API_KEY}
    assert len(mock_setup_entry.mock_calls) == 1