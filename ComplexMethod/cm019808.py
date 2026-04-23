async def test_flow_reauth_errors(
    hass: HomeAssistant,
    habitica: AsyncMock,
    config_entry: MockConfigEntry,
    raise_error: Exception,
    user_input: dict[str, Any],
    text_error: str,
) -> None:
    """Test reauth flow with invalid credentials."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    habitica.get_user.side_effect = raise_error
    habitica.login.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    habitica.get_user.side_effect = None
    habitica.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_REAUTH_API_KEY,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_API_KEY] == "cd0e5985-17de-4b4f-849e-5d506c5e4382"

    assert len(hass.config_entries.async_entries()) == 1