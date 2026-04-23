async def test_reauth_with_authentication_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pvoutput: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the reauthentication configuration flow with an authentication error.

    This tests tests a reauth flow, with a case the user enters an invalid
    API key, but recover by entering the correct one.
    """
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    mock_pvoutput.system.side_effect = PVOutputAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "invalid_key"},
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "reauth_confirm"
    assert result2.get("errors") == {"base": "invalid_auth"}

    assert len(mock_setup_entry.mock_calls) == 0
    assert len(mock_pvoutput.system.mock_calls) == 1

    mock_pvoutput.system.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_API_KEY: "valid_key"},
    )
    await hass.async_block_till_done()

    assert result3.get("type") is FlowResultType.ABORT
    assert result3.get("reason") == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_SYSTEM_ID: 12345,
        CONF_API_KEY: "valid_key",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_pvoutput.system.mock_calls) == 2