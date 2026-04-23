async def test_full_user_flow_single_installation_with_mfa(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
) -> None:
    """Test a full user initiated flow with a single installation and mfa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    mock_verisure_config_flow.login.side_effect = VerisureLoginError(
        "Multifactor authentication enabled, disable or create MFA cookie"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "email": "verisure_my_pages@example.com",
            "password": "SuperS3cr3t!",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "mfa"

    mock_verisure_config_flow.login.side_effect = None
    mock_verisure_config_flow.get_installations.return_value = {
        k1: {k2: {k3: [v3[0]] for k3, v3 in v2.items()} for k2, v2 in v1.items()}
        for k1, v1 in mock_verisure_config_flow.get_installations.return_value.items()
    }

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "code": "123456",
        },
    )
    await hass.async_block_till_done()

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "ascending (12345th street)"
    assert result3.get("data") == {
        CONF_GIID: "12345",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "SuperS3cr3t!",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 1
    assert len(mock_verisure_config_flow.request_mfa.mock_calls) == 1
    assert len(mock_verisure_config_flow.validate_mfa.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1