async def test_form_login_errors(
    hass: HomeAssistant, habitica: AsyncMock, raise_error, text_error
) -> None:
    """Test we handle invalid credentials error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "login"},
    )

    habitica.login.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_LOGIN_STEP,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    # recover from errors
    habitica.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_LOGIN_STEP,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-user"
    assert result["data"] == {
        CONF_API_USER: TEST_API_USER,
        CONF_API_KEY: TEST_API_KEY,
        CONF_URL: DEFAULT_URL,
        CONF_VERIFY_SSL: True,
    }
    assert result["result"].unique_id == TEST_API_USER