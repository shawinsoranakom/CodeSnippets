async def test_flow_reconfigure_errors(
    hass: HomeAssistant,
    habitica: AsyncMock,
    config_entry: MockConfigEntry,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test reconfigure flow errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    habitica.get_user.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    habitica.get_user.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_API_KEY] == "cd0e5985-17de-4b4f-849e-5d506c5e4382"
    assert config_entry.data[CONF_URL] == DEFAULT_URL
    assert config_entry.data[CONF_VERIFY_SSL] is True

    assert len(hass.config_entries.async_entries()) == 1