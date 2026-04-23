async def test_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_server: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test we get the form and handle errors and successful connection."""

    mock_server.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    mock_server.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY