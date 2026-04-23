async def test_form_exceptions(
    hass: HomeAssistant,
    exception: Exception,
    error: str,
    mock_setup_entry: AsyncMock,
    mock_aquacell_api: AsyncMock,
) -> None:
    """Test we handle form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_aquacell_api.authenticate.side_effect = exception
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": error}

    mock_aquacell_api.authenticate.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == TEST_CONFIG_ENTRY[CONF_EMAIL]
    assert result3["data"][CONF_EMAIL] == TEST_CONFIG_ENTRY[CONF_EMAIL]
    assert result3["data"][CONF_PASSWORD] == TEST_CONFIG_ENTRY[CONF_PASSWORD]
    assert result3["data"][CONF_REFRESH_TOKEN] == TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN]
    assert result3["data"][CONF_BRAND] == TEST_CONFIG_ENTRY[CONF_BRAND]
    assert len(mock_setup_entry.mock_calls) == 1