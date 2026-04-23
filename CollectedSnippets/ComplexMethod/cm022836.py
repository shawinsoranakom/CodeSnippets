async def test_reconfigure_success(hass: HomeAssistant, fritz: Mock) -> None:
    """Test starting a reconfigure flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)

    assert mock_config.data[CONF_HOST] == "10.0.0.1"
    assert mock_config.data[CONF_USERNAME] == "fake_user"
    assert mock_config.data[CONF_PASSWORD] == "fake_pass"

    result = await mock_config.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "new_host",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config.data[CONF_HOST] == "new_host"
    assert mock_config.data[CONF_USERNAME] == "fake_user"
    assert mock_config.data[CONF_PASSWORD] == "fake_pass"