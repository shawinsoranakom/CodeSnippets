async def test_reauth(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_solarlog_connector: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reauth-flow works."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        data={
            CONF_HOST: HOST,
            CONF_HAS_PWD: True,
            CONF_PASSWORD: "pwd",
        },
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_solarlog_connector.test_extended_data_available.side_effect = exception

    # tests with connection error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "other_pwd"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == error

    mock_solarlog_connector.test_extended_data_available.side_effect = None

    # tests with all information provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "other_pwd"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "other_pwd"