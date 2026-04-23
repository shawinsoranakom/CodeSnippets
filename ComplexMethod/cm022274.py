async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_aquacell_api: AsyncMock
) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == TEST_CONFIG_ENTRY[CONF_EMAIL]
    assert result2["data"][CONF_EMAIL] == TEST_CONFIG_ENTRY[CONF_EMAIL]
    assert result2["data"][CONF_PASSWORD] == TEST_CONFIG_ENTRY[CONF_PASSWORD]
    assert result2["data"][CONF_REFRESH_TOKEN] == TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN]
    assert result2["data"][CONF_BRAND] == TEST_CONFIG_ENTRY[CONF_BRAND]
    assert len(mock_setup_entry.mock_calls) == 1