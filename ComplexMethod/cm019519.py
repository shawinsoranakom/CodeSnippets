async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_solarlog_connector: AsyncMock,
    has_password: bool,
    password: str,
) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        data={
            CONF_HOST: HOST,
            CONF_HAS_PWD: False,
        },
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # test with all data provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HAS_PWD: True, CONF_PASSWORD: password}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert len(mock_setup_entry.mock_calls) == 1

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert entry
    assert entry.title == HOST
    assert entry.data[CONF_HAS_PWD] == has_password
    assert entry.data[CONF_PASSWORD] == password