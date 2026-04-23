async def test_flow_reconfigure_errors(
    hass: HomeAssistant,
    mock_aiontfy: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test reconfigure flow errors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: None,
            CONF_TOKEN: None,
        },
    )
    mock_aiontfy.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    mock_aiontfy.account.side_effect = exception

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_aiontfy.account.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "username", CONF_PASSWORD: "password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_USERNAME] == "username"
    assert config_entry.data[CONF_TOKEN] == "newtoken"

    assert len(hass.config_entries.async_entries()) == 1