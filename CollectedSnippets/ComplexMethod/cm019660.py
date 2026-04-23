async def test_form_user(hass: HomeAssistant, mock_ghost_api: AsyncMock) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Ghost"
    assert result["result"].unique_id == SITE_UUID
    assert result["data"] == {
        CONF_API_URL: API_URL,
        CONF_ADMIN_API_KEY: API_KEY,
    }