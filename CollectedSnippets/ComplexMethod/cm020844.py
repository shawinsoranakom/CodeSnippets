async def test_user(hass: HomeAssistant, mock_ttnclient) -> None:
    """Test user config."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_DATA,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == APP_ID
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_APP_ID] == APP_ID
    assert result["data"][CONF_API_KEY] == API_KEY