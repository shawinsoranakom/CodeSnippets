async def test_form_auth_invalid_credentials(
    hass: HomeAssistant, ics_content: str
) -> None:
    """Test wrong credentials in auth step shows invalid_auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    respx.get(CALENDER_URL).mock(
        return_value=Response(
            status_code=401,
            headers={"www-authenticate": 'Basic realm="test"'},
        )
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CALENDAR_NAME: CALENDAR_NAME,
            CONF_URL: CALENDER_URL,
            CONF_VERIFY_SSL: True,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "auth"

    # Wrong credentials - server still returns 401
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "wrong",
            CONF_PASSWORD: "wrong",
        },
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "auth"
    assert result3["errors"] == {"base": "invalid_auth"}

    # Correct credentials
    respx.get(CALENDER_URL).mock(
        return_value=Response(
            status_code=200,
            text=ics_content,
        )
    )
    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
        },
    )
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == CALENDAR_NAME