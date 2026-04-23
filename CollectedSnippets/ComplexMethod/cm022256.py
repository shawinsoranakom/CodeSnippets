async def test_reauth(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_fyta_connector: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reauth-flow works."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            CONF_ACCESS_TOKEN: ACCESS_TOKEN,
            CONF_EXPIRATION: EXPIRATION,
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_fyta_connector.login.side_effect = exception

    # tests with connection error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == error

    mock_fyta_connector.login.side_effect = None

    # tests with all information provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "other_username", CONF_PASSWORD: "other_password"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_USERNAME] == "other_username"
    assert entry.data[CONF_PASSWORD] == "other_password"
    assert entry.data[CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert entry.data[CONF_EXPIRATION] == EXPIRATION