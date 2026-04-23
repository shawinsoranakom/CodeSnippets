async def test_configure_entry(
    hass: HomeAssistant, mock_rehlko: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we can configure the entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

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