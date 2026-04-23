async def test_user(hass: HomeAssistant, fritz: Mock) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.0.0.1"
    assert result["data"][CONF_HOST] == "10.0.0.1"
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert not result["result"].unique_id