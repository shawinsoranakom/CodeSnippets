async def test_configure_entry_exceptions(
    hass: HomeAssistant,
    mock_rehlko: AsyncMock,
    error: Exception,
    conf_error: dict[str, str],
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we handle a variety of exceptions and recover by adding new entry."""
    # First try to authenticate and get an error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_rehlko.authenticate.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: TEST_EMAIL,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == conf_error
    assert mock_setup_entry.call_count == 0

    # Now try to authenticate again and succeed
    # This should create a new entry
    mock_rehlko.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: TEST_EMAIL,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_EMAIL.lower()
    assert result["data"] == {
        CONF_EMAIL: TEST_EMAIL,
        CONF_PASSWORD: TEST_PASSWORD,
    }
    assert result["result"].unique_id == TEST_SUBJECT
    assert mock_setup_entry.call_count == 1