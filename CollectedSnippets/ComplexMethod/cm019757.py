async def test_reauth_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
    error: str,
) -> None:
    """Test a reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    mock_verisure_config_flow.login.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "WrOngP4ssw0rd!",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("step_id") == "reauth_confirm"
    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("errors") == {"base": error}

    mock_verisure_config_flow.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )
    mock_verisure_config_flow.request_mfa.side_effect = side_effect

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("step_id") == "reauth_confirm"
    assert result3.get("errors") == {"base": "unknown_mfa"}

    mock_verisure_config_flow.request_mfa.side_effect = None

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    assert result4.get("type") is FlowResultType.FORM
    assert result4.get("step_id") == "reauth_mfa"

    mock_verisure_config_flow.validate_mfa.side_effect = side_effect

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {
            "code": "123456",
        },
    )
    assert result5.get("type") is FlowResultType.FORM
    assert result5.get("step_id") == "reauth_mfa"
    assert result5.get("errors") == {"base": error}

    mock_verisure_config_flow.validate_mfa.side_effect = None
    mock_verisure_config_flow.login.side_effect = None
    mock_verisure_config_flow.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in mock_verisure_config_flow.get_installations.return_value.items()
    }

    await hass.config_entries.flow.async_configure(
        result5["flow_id"],
        {
            "code": "654321",
        },
    )
    await hass.async_block_till_done()

    assert mock_config_entry.data == {
        CONF_GIID: "12345",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "SuperS3cr3t!",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 4
    assert len(mock_verisure_config_flow.request_mfa.mock_calls) == 2
    assert len(mock_verisure_config_flow.validate_mfa.mock_calls) == 2
    assert len(mock_setup_entry.mock_calls) == 1