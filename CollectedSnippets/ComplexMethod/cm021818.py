async def test_form_zeroconf(hass: HomeAssistant) -> None:
    """Test we can setup from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            hostname="mock_hostname",
            name="mock_name",
            port=1234,
            properties={},
            type="mock_type",
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "192.168.1.5:1234"
    assert result2["data"] == {
        CONF_HOST: "192.168.1.5",
        CONF_PASSWORD: "test-password",
        CONF_PORT: 1234,
        CONF_USERNAME: "test-username",
    }
    assert result2["result"].unique_id is None
    assert len(mock_setup_entry.mock_calls) == 1