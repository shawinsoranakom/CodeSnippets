async def test_full_user_flow_multiple_installations_with_mfa(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_verisure_config_flow: MagicMock,
) -> None:
    """Test a full user initiated configuration flow with a single installation."""
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

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "code": "123456",
        },
    )
    await hass.async_block_till_done()

    assert result3.get("step_id") == "installation"
    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("errors") is None

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"], {"giid": "54321"}
    )
    await hass.async_block_till_done()

    assert result4.get("type") is FlowResultType.CREATE_ENTRY
    assert result4.get("title") == "descending (54321th street)"
    assert result4.get("data") == {
        CONF_GIID: "54321",
        CONF_EMAIL: "verisure_my_pages@example.com",
        CONF_PASSWORD: "SuperS3cr3t!",
    }

    assert len(mock_verisure_config_flow.login.mock_calls) == 1
    assert len(mock_verisure_config_flow.request_mfa.mock_calls) == 1
    assert len(mock_verisure_config_flow.validate_mfa.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1