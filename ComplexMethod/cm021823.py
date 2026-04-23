async def test_reconfigure_one_alias_password_nochange(hass: HomeAssistant) -> None:
    """Test reconfigure one alias when there is no password change."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 456,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: PASSWORD_NOT_CHANGED,
            },
        )

        assert result2["type"] is FlowResultType.ABORT
        assert result2["reason"] == "reconfigure_successful"

        assert entry.data[CONF_HOST] == "2.2.2.2"
        assert entry.data[CONF_PORT] == 456
        assert entry.data[CONF_USERNAME] == "test-new-username"
        assert entry.data[CONF_PASSWORD] == "test-password"