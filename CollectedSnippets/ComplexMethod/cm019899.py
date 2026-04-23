async def test_async_step_user_success(
    hass: HomeAssistant, mock_compit_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test user step with successful authentication."""
    mock_compit_api.return_value = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == config_entries.SOURCE_USER
    assert result["description_placeholders"] == {
        "compit_url": "https://inext.compit.pl/"
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == CONFIG_INPUT[CONF_EMAIL]
    assert result["data"] == CONFIG_INPUT
    assert len(mock_setup_entry.mock_calls) == 1