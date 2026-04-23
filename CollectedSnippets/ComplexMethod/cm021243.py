async def test_async_step_reauth_invalid_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_omada_client: MagicMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test reauth handles various exceptions."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_omada_client.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "new_uname", CONF_PASSWORD: "new_passwd"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": expected_error}

    mock_omada_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "new_uname", CONF_PASSWORD: "new_passwd"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"