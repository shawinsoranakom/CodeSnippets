async def test_reconfigure_one_alias_already_configured(hass: HomeAssistant) -> None:
    """Test reconfigure when config changed to an existing host/port/alias."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    entry2 = await async_init_integration(
        hass,
        host="2.2.2.2",
        port=456,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry2.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: int(entry.data[CONF_PORT]),
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        assert result2["type"] is FlowResultType.ABORT
        assert result2["reason"] == "already_configured"

        assert entry.data[CONF_HOST] == "1.1.1.1"
        assert entry.data[CONF_PORT] == 123
        assert entry.data[CONF_USERNAME] == "test-username"
        assert entry.data[CONF_PASSWORD] == "test-password"

        assert entry2.data[CONF_HOST] == "2.2.2.2"
        assert entry2.data[CONF_PORT] == 456
        assert entry2.data[CONF_USERNAME] == "test-username"
        assert entry2.data[CONF_PASSWORD] == "test-password"