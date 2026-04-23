async def test_unknown_state(hass: HomeAssistant, mock_syncthru: AsyncMock) -> None:
    """Test we show user form on unsupported device."""
    mock_syncthru.is_unknown_state.return_value = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_URL: "unknown_state"}

    mock_syncthru.is_unknown_state.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY