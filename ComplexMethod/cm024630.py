async def test_form_reauth_errors(
    hass: HomeAssistant,
    mock_aiontfy: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test reauth flow errors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            CONF_USERNAME: "username",
            CONF_TOKEN: "token",
        },
    )
    mock_aiontfy.account.side_effect = exception
    mock_aiontfy.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "password"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_aiontfy.account.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "password"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data == {
        CONF_URL: "https://ntfy.sh/",
        CONF_USERNAME: "username",
        CONF_TOKEN: "newtoken",
    }
    assert len(hass.config_entries.async_entries()) == 1