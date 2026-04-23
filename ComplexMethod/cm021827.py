async def test_reconfigure_multiple_aliases_password_nochange(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure with multiple aliases when no password change."""
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
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={"battery.voltage": "voltage"},
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

        assert result2["type"] is FlowResultType.FORM
        assert result2["step_id"] == "reconfigure_ups"

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

        assert result3["type"] is FlowResultType.ABORT
        assert result3["reason"] == "reconfigure_successful"

        assert entry.data[CONF_HOST] == "2.2.2.2"
        assert entry.data[CONF_PORT] == 456
        assert entry.data[CONF_USERNAME] == "test-new-username"
        assert entry.data[CONF_PASSWORD] == "test-password"
        assert entry.data[CONF_ALIAS] == "ups2"