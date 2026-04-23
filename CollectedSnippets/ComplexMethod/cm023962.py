async def test_full_user_flow_advanced_options(
    hass: HomeAssistant,
    mock_sonarr_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the full manual user flow with advanced options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER, "show_advanced_options": True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    user_input = {
        **MOCK_USER_INPUT,
        CONF_VERIFY_SSL: True,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "192.168.1.189"

    assert result["data"]
    assert result["data"][CONF_URL] == "http://192.168.1.189:8989/"
    assert result["data"][CONF_VERIFY_SSL]