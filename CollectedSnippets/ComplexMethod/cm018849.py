async def test_async_step_reauth_confirm_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    get_client: AirPatrolAPI,
) -> None:
    """Test reauthentication failure due to invalid credentials."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.airpatrol.config_flow.AirPatrolAPI.authenticate",
        side_effect=AirPatrolAuthenticationError("fail"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=TEST_USER_INPUT
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {"base": "invalid_auth"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == "test_password"
    assert mock_config_entry.data[CONF_ACCESS_TOKEN] == "test_access_token"