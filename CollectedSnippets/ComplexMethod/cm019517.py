async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_HAS_PWD: False},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == HOST
    assert result2["data"][CONF_HOST] == "http://1.1.1.1"
    assert result2["data"][CONF_HAS_PWD] is False
    assert len(mock_setup_entry.mock_calls) == 1