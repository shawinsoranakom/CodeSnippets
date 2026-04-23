async def test_reauth_not_successful(
    hass: HomeAssistant,
    mock_vedo: AsyncMock,
    mock_vedo_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    mock_vedo_config_entry.add_to_hass(hass)
    result = await mock_vedo_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_vedo.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: FAKE_PIN,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": error}

    mock_vedo.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PIN: VEDO_PIN,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_vedo_config_entry.data[CONF_PIN] == VEDO_PIN