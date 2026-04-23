async def test_flow_fails(
    hass: HomeAssistant, error: Exception, message: str, default_user: MockUser
) -> None:
    """Test user initialized flow with invalid username."""
    with patch("pylast.User", return_value=MockUser(thrown_error=error)):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_USER_DATA
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == message

    with patch("pylast.User", return_value=default_user), patch_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_USER_DATA,
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]
        assert result["step_id"] == "friends"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONF_FRIENDS_DATA
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == DEFAULT_NAME
        assert result["options"] == CONF_DATA