async def test_auth_flow_success(
    hass: HomeAssistant,
    mock_get_server_info: AsyncMock,
) -> None:
    """Test successful authentication flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth_manual"

    with patch("homeassistant.components.music_assistant.config_flow._test_connection"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: "test_auth_token"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        CONF_URL: "http://localhost:8095",
        CONF_TOKEN: "test_auth_token",
    }
    assert result["result"].unique_id == "1234"