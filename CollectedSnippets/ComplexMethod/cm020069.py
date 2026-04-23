async def test_step_reauth(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test reauth flow."""
    new_password = "ABCD"
    new_client_id = "EFGH"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # test PyViCareInvalidConfigurationError
    with patch(
        f"{MODULE}.config_flow.login",
        side_effect=PyViCareInvalidConfigurationError(
            {"error": "foo", "error_description": "bar"}
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password, CONF_CLIENT_ID: new_client_id},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {"base": "invalid_auth"}

    # test success
    with patch(
        f"{MODULE}.config_flow.login",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password, CONF_CLIENT_ID: new_client_id},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

        assert len(hass.config_entries.async_entries()) == 1
        assert (
            hass.config_entries.async_entries()[0].data[CONF_PASSWORD] == new_password
        )
        assert (
            hass.config_entries.async_entries()[0].data[CONF_CLIENT_ID] == new_client_id
        )
        await hass.async_block_till_done()